"""
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import os
import logging
from typing import Dict, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import googlemaps
from datetime import datetime

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")
        self.gmaps = googlemaps.Client(key=api_key)

    def _get_decimal_coordinates(self, gps_coords: Dict) -> Optional[tuple[float, float]]:
        """Convert GPS coordinates from degrees/minutes/seconds to decimal format"""
        try:
            lat_data = gps_coords.get('GPSLatitude')
            lat_ref = gps_coords.get('GPSLatitudeRef', 'N')
            lon_data = gps_coords.get('GPSLongitude')
            lon_ref = gps_coords.get('GPSLongitudeRef', 'E')

            if not all([lat_data, lon_data]):
                return None

            def convert_to_degrees(value):
                d, m, s = value
                degrees = float(d)
                minutes = float(m)
                seconds = float(s)
                return degrees + (minutes / 60.0) + (seconds / 3600.0)

            lat = convert_to_degrees(lat_data)
            lon = convert_to_degrees(lon_data)

            if lat_ref == 'S':
                lat = -lat
            if lon_ref == 'W':
                lon = -lon

            return (lat, lon)
        except Exception as e:
            logger.error(f"Error converting GPS coordinates: {str(e)}")
            return None

    def extract_location_from_image(self, image_path: str) -> Optional[Dict]:
        """Extract location information from image EXIF data"""
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if not exif:
                    return None

                gps_info = {}
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'GPSInfo':
                        for gps_tag in exif[tag_id]:
                            sub_tag = GPSTAGS.get(gps_tag, gps_tag)
                            gps_info[sub_tag] = exif[tag_id][gps_tag]

                coordinates = self._get_decimal_coordinates(gps_info)
                if not coordinates:
                    return None

                return self.get_location_details(coordinates[0], coordinates[1])
        except Exception as e:
            logger.error(f"Error extracting location from image: {str(e)}")
            return None

    def get_location_details(self, latitude: float, longitude: float) -> Dict:
        """Get location details from Google Maps API"""
        try:
            reverse_geocode_result = self.gmaps.reverse_geocode((latitude, longitude))
            
            if not reverse_geocode_result:
                return None

            location_data = reverse_geocode_result[0]
            
            # Extract relevant information
            location_details = {
                'formatted_address': location_data.get('formatted_address'),
                'latitude': latitude,
                'longitude': longitude,
                'place_id': location_data.get('place_id'),
                'components': {}
            }

            # Extract address components
            for component in location_data.get('address_components', []):
                types = component.get('types', [])
                if 'country' in types:
                    location_details['components']['country'] = component.get('long_name')
                elif 'administrative_area_level_1' in types:
                    location_details['components']['state'] = component.get('long_name')
                elif 'locality' in types:
                    location_details['components']['city'] = component.get('long_name')
                elif 'postal_code' in types:
                    location_details['components']['postal_code'] = component.get('long_name')

            return location_details

        except Exception as e:
            logger.error(f"Error getting location details: {str(e)}")
            return None