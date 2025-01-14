import os
import requests
import json
from pathlib import Path
import time
from typing import List, Dict
import re
from PIL import Image
import io
import math

class WikipediaImageDownloader:
    def __init__(self):
        """
        Initialize the downloader with Wikipedia API endpoint
        """
        self.api_endpoint = "https://en.wikipedia.org/w/api.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_page_images(self, title: str, num_images: int = 70) -> List[str]:
        """
        Get images from a Wikipedia page using the API
        """
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "images",
            "imlimit": "500"  # Request more images to filter out non-relevant ones
        }

        try:
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract page ID
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return []

            page_id = list(pages.keys())[0]
            images = pages[page_id].get("images", [])

            # Filter out non-image files and get image titles
            image_titles = [
                img["title"] for img in images 
                if any(ext in img["title"].lower() for ext in [".jpg", ".jpeg", ".png"]) 
                and not any(skip in img["title"].lower() for skip in ["logo", "icon", "map", "symbol", "flag", "diagram", "scheme"])
            ]

            # Now get the actual URLs for these images
            image_urls = []
            for title in image_titles[:num_images]:
                img_url = self.get_image_url(title)
                if img_url:
                    image_urls.append(img_url)

            return image_urls[:num_images]

        except Exception as e:
            print(f"Error getting images for {title}: {str(e)}")
            return []

    def get_image_url(self, image_title: str) -> str:
        """
        Get the actual URL for an image using its title
        """
        params = {
            "action": "query",
            "format": "json",
            "titles": image_title,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        try:
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return ""

            page_id = list(pages.keys())[0]
            image_info = pages[page_id].get("imageinfo", [])
            
            if image_info:
                return image_info[0].get("url", "")

        except Exception as e:
            print(f"Error getting image URL for {image_title}: {str(e)}")
        
        return ""

    def resize_image_to_max_size(self, img: Image.Image, max_size_mb: float = 0.5) -> Image.Image:
        """
        Resize an image to ensure its file size is under 500KB
        """
        # Convert max size to bytes (500KB = 0.5MB)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Save to a temporary buffer to check size
        temp_buffer = io.BytesIO()
        img.save(temp_buffer, format='JPEG', quality=95)
        current_size = temp_buffer.tell()
        
        # If size is already OK, return original
        if current_size <= max_size_bytes:
            return img
        
        # Calculate scaling factor based on size ratio
        scale_factor = math.sqrt(max_size_bytes / current_size)
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        
        # Resize image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Fine-tune quality if still too large
        quality = 95
        while quality > 50:
            temp_buffer = io.BytesIO()
            resized_img.save(temp_buffer, format='JPEG', quality=quality)
            if temp_buffer.tell() <= max_size_bytes:
                break
            quality -= 5
        
        return resized_img

    def download_image(self, url: str, filepath: Path) -> bool:
        """
        Download an image from URL, resize if necessary, and save it to the specified path
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)  # Add timeout
            response.raise_for_status()

            # Ensure the directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Load image into PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary (handles PNG with transparency)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            
            # Resize if needed
            img = self.resize_image_to_max_size(img, max_size_mb=0.5)
            
            # Save the image
            img.save(filepath, 'JPEG', quality=95)
            return True

        except requests.exceptions.Timeout:
            print(f" ✗ (timeout)")
            return False
        except requests.exceptions.RequestException as e:
            print(f" ✗ (network error: {str(e)})")
            return False
        except Exception as e:
            print(f" ✗ (error: {str(e)})")
            return False

    def create_location_folders(self, base_path: str, locations: Dict[str, str], images_per_location: int = 3) -> None:
        """
        Create folders for each location and download images into them
        """
        base_path = Path(base_path)
        base_path.mkdir(exist_ok=True)

        total_locations = len(locations)
        current_location = 0

        for folder_name, wiki_title in locations.items():
            current_location += 1
            print(f"\nProcessing location [{current_location}/{total_locations}]: {folder_name}")
            location_path = base_path / folder_name
            location_path.mkdir(exist_ok=True)
            
            # Get images for the location
            image_urls = self.get_page_images(wiki_title, images_per_location)
            
            if not image_urls:
                print(f"No images found for {folder_name}")
                continue

            total_images = len(image_urls)
            successful_downloads = 0
            
            print(f"Found {total_images} images to download")
            
            for idx, image_url in enumerate(image_urls):
                if image_url:
                    try:
                        # Create filename with location and index
                        file_extension = image_url.split('.')[-1].lower()
                        if len(file_extension) > 4 or file_extension not in ['jpg', 'jpeg', 'png']:  # Handle cases where URL has parameters
                            file_extension = 'jpg'
                        filename = f"{folder_name}_{idx + 1}.{file_extension}"
                        filepath = location_path / filename
                        
                        # Skip if file already exists
                        if filepath.exists():
                            print(f"Skipping {filename} - already exists")
                            successful_downloads += 1
                            continue
                        
                        print(f"Downloading image [{idx + 1}/{total_images}] for {folder_name}...", end='', flush=True)
                        if self.download_image(image_url, filepath):
                            successful_downloads += 1
                            print(" ✓")
                        else:
                            print(" ✗")
                        
                        # Add a small delay between downloads to avoid rate limiting
                        time.sleep(0.5)
                    
                    except Exception as e:
                        print(f"\nError downloading {image_url}: {str(e)}")
                        continue
            
            print(f"Successfully downloaded {successful_downloads} images for {folder_name}")

def main():
    # Dictionary mapping folder names to Wikipedia page titles
    # Comprehensive list of power plants around the world
    locations = {
        # International Power Plants
        "Three_Gorges_Dam": "Three_Gorges_Dam",  # Hydroelectric
        "Itaipu_Dam": "Itaipu_Dam",  # Hydroelectric
        "Kashiwazaki_Kariwa": "Kashiwazaki-Kariwa_Nuclear_Power_Plant",  # Nuclear
        "Belchatow_Power_Station": "Bełchatów_Power_Station",  # Coal
        "Surgut_Power_Station": "Surgut-2_Power_Station",  # Natural Gas
        "Geysers_Geothermal": "The_Geysers",  # Geothermal
        "Ivanpah_Solar": "Ivanpah_Solar_Power_Facility",  # Solar Thermal
        "Gansu_Wind_Farm": "Gansu_Wind_Farm",  # Wind
        "Tengger_Desert_Solar": "Tengger_Desert_Solar_Park",  # Solar PV
        "Drax_Power_Station": "Drax_Power_Station",  # Biomass/Coal
        "Rance_Tidal": "Rance_Tidal_Power_Station",  # Tidal
        "Cruas_Nuclear": "Cruas_Nuclear_Power_Plant",  # Nuclear
        "Taichung_Power_Plant": "Taichung_Power_Plant",  # Coal
        "Sayano_Shushenskaya": "Sayano–Shushenskaya_Dam",  # Hydroelectric
        "Topaz_Solar": "Topaz_Solar_Farm",  # Solar PV
        "Alta_Wind_Energy": "Alta_Wind_Energy_Center",  # Wind
        "Olkiluoto_Nuclear": "Olkiluoto_Nuclear_Power_Plant",  # Nuclear
        "Hoover_Dam": "Hoover_Dam",  # Hydroelectric
        "Hellisheidi_Geothermal": "Hellisheiði_Power_Station",  # Geothermal
        "Xiluodu_Dam": "Xiluodu_Dam",  # Hydroelectric
        "Shoaiba_Power_Plant": "Shoaiba_Power_Plant",  # Oil/Gas
        "Tuoketuo_Power_Station": "Tuoketuo_Power_Station",  # Coal
        "Taishan_Nuclear": "Taishan_Nuclear_Power_Plant",  # Nuclear
        "Pavagada_Solar_Park": "Pavagada_Solar_Park",  # Solar
        "London_Array": "London_Array",  # Offshore Wind
        "Cernavoda_Nuclear": "Cernavodă_Nuclear_Power_Plant",  # Nuclear
        "Ertan_Dam": "Ertan_Dam",  # Hydroelectric
        "Guodian_Beilun": "Guodian_Beilun_Power_Station",  # Coal
        "Futtsu_Power_Station": "Futtsu_Power_Station",  # Natural Gas
        "Wayang_Windu": "Wayang_Windu_Power_Station",  # Geothermal

        # Brazilian Hydroelectric Power Plants
        "Belo_Monte": "Belo_Monte_Dam",  # Hydroelectric
        "Tucurui": "Tucuruí_Dam",  # Hydroelectric
        "Ilha_Solteira": "Ilha_Solteira_Dam",  # Hydroelectric
        "Jupia": "Engenheiro_Souza_Dias_Dam",  # Hydroelectric (Jupiá)
        "Xingo": "Xingó_Dam",  # Hydroelectric
        "Paulo_Afonso": "Paulo_Afonso_Hydroelectric_Complex",  # Hydroelectric
        "Furnas": "Furnas_Dam",  # Hydroelectric
        "Emborcacao": "Emborcação_Dam",  # Hydroelectric
        "Tres_Marias": "Três_Marias_Dam",  # Hydroelectric
        "Porto_Primavera": "Porto_Primavera_Dam",  # Hydroelectric
        "Sobradinho": "Sobradinho_Dam",  # Hydroelectric
        "Itumbiara": "Itumbiara_Dam",  # Hydroelectric
        "Machadinho": "Machadinho_Dam",  # Hydroelectric
        "Salto_Santiago": "Salto_Santiago_Dam",  # Hydroelectric
        "Salto_Osorio": "Salto_Osório_Dam",  # Hydroelectric
        "Agua_Vermelha": "Água_Vermelha_Dam",  # Hydroelectric
        "Irape": "Irapé_Dam",  # Hydroelectric
        "Corumba": "Corumbá_Dam",  # Hydroelectric
        "Serra_da_Mesa": "Serra_da_Mesa_Dam",  # Hydroelectric
        "Nova_Ponte": "Nova_Ponte_Dam",  # Hydroelectric
        "Capivara": "Capivara_Dam",  # Hydroelectric
        "Foz_do_Areia": "Foz_do_Areia_Dam",  # Hydroelectric
        "Chavantes": "Chavantes_Dam",  # Hydroelectric
        "Barra_Bonita": "Barra_Bonita_Dam",  # Hydroelectric
        "Volta_Grande": "Volta_Grande_Dam",  # Hydroelectric
        "Funil": "Funil_Dam",  # Hydroelectric
        "Moxoto": "Moxotó_Dam",  # Hydroelectric
        "Mascarenhas_de_Moraes": "Mascarenhas_de_Moraes_Dam",  # Hydroelectric

        # Brazilian Thermal Power Plants
        "UTE_Norte_Fluminense": "Norte_Fluminense_Thermal_Power_Plant",  # Thermal
        "UTE_Porto_do_Pecem": "Porto_do_Pecém_Thermal_Power_Plant",  # Thermal
        "UTE_Uruguaiana": "Uruguaiana_Thermal_Power_Plant",  # Thermal
        "UTE_Cuiaba": "Cuiabá_Thermal_Power_Plant",  # Thermal
        "UTE_Jorge_Lacerda": "Jorge_Lacerda_Thermal_Power_Plant",  # Thermal
        "UTE_Maua": "Mauá_Thermal_Power_Plant",  # Thermal
        "UTE_Candiota": "Candiota_Thermal_Power_Plant",  # Thermal
        "UTE_Araucaria": "Araucária_Thermal_Power_Plant",  # Thermal
        "UTE_Fortaleza": "Fortaleza_Thermal_Power_Plant",  # Thermal
        "UTE_Termorio": "Governador_Leonel_Brizola_Thermal_Power_Plant",  # Thermal
        "UTE_Presidente_Medici": "Presidente_Médici_Thermal_Power_Plant",  # Thermal
        "UTE_Piratininga": "Piratininga_Thermal_Power_Plant",  # Thermal
        "UTE_Santa_Cruz": "Santa_Cruz_Thermal_Power_Plant",  # Thermal
        "UTE_Termopernambuco": "Termopernambuco_Power_Plant",  # Thermal
        "UTE_Juiz_de_Fora": "Juiz_de_Fora_Thermal_Power_Plant",  # Thermal
        "UTE_Termobahia": "Termobahia_Power_Plant",  # Thermal

        # Brazilian Wind Farms
        "Complexo_Alto_Sertao": "Alto_Sertão_Wind_Complex",  # Wind
        "Complexo_Campos_Neutrais": "Campos_Neutrais_Wind_Complex",  # Wind
        "Complexo_Chapada_Diamantina": "Chapada_Diamantina_Wind_Complex",  # Wind
        "Complexo_Ventos_do_Sul": "Ventos_do_Sul_Wind_Complex",  # Wind
        "Complexo_Santo_Agostinho": "Santo_Agostinho_Wind_Complex",  # Wind
        "Complexo_Rio_do_Fogo": "Rio_do_Fogo_Wind_Complex",  # Wind
        "Complexo_Trairi": "Trairi_Wind_Complex",  # Wind
        "Complexo_Santa_Vitoria": "Santa_Vitória_do_Palmar_Wind_Complex",  # Wind
        "Complexo_Areia_Branca": "Areia_Branca_Wind_Complex",  # Wind
        "Parque_Eolico_Osorio": "Osório_Wind_Farm",  # Wind
        "Parque_Eolico_Caetes": "Caetés_Wind_Farm",  # Wind
        "Parque_Eolico_Eurus": "Eurus_Wind_Farm",  # Wind

        # Brazilian Solar Plants
        "Usina_Solar_Nova_Olinda": "Nova_Olinda_Solar_Plant",  # Solar
        "Usina_Solar_Ituverava": "Ituverava_Solar_Plant",  # Solar
        "Usina_Solar_Pirapora": "Pirapora_Solar_Complex",  # Solar
        "Usina_Solar_Sao_Goncalo": "São_Gonçalo_Solar_Plant",  # Solar
        "Usina_Solar_Guaimarania": "Guimarânia_Solar_Plant",  # Solar
        "Usina_Solar_Coremas": "Coremas_Solar_Plant",  # Solar
        "Usina_Solar_Janauba": "Janaúba_Solar_Plant",  # Solar
        "Usina_Solar_Bom_Jesus": "Bom_Jesus_da_Lapa_Solar_Plant",  # Solar

        # Brazilian Nuclear Plants
        "Angra_1": "Angra_Nuclear_Power_Plant",  # Nuclear
        "Angra_2": "Angra_Nuclear_Power_Plant",  # Nuclear
        "Angra_3": "Angra_Nuclear_Power_Plant",  # Nuclear

        # Additional Latin American Power Plants
        
        # Argentina
        "Atucha_Nuclear": "Atucha_Nuclear_Power_Plant",  # Nuclear
        "Embalse_Nuclear": "Embalse_Nuclear_Power_Station",  # Nuclear
        "Yacyreta_Dam": "Yacyretá_Dam",  # Hydroelectric
        "Salto_Grande_Dam": "Salto_Grande_Dam",  # Hydroelectric
        "Piedra_del_Aguila": "Piedra_del_Águila_Dam",  # Hydroelectric
        "El_Chocon": "El_Chocón_Dam",  # Hydroelectric
        "Alicura_Dam": "Alicurá_Dam",  # Hydroelectric
        "Futaleufú_Dam": "Futaleufú_Dam",  # Hydroelectric
        "Central_Puerto": "Central_Puerto_Power_Station",  # Thermal
        "Cauchari_Solar": "Cauchari_Solar_Project",  # Solar

        # Chile
        "Ralco_Dam": "Ralco_Dam",  # Hydroelectric
        "Pangue_Dam": "Pangue_Dam",  # Hydroelectric
        "Alto_Maipo": "Alto_Maipo_Hydroelectric_Project",  # Hydroelectric
        "Atacama_Solar": "Atacama_Solar_Platform",  # Solar
        "Maria_Elena_Solar": "María_Elena_Solar_Power_Plant",  # Solar
        "Cerro_Dominador": "Cerro_Dominador_Solar_Thermal_Plant",  # Solar Thermal
        "San_Isidro_Power": "San_Isidro_Power_Station",  # Thermal
        "Mejillones_Power": "Mejillones_Power_Station",  # Thermal
        "Tarapaca_Power": "Tarapacá_Power_Plant",  # Thermal

        # Colombia
        "El_Guavio": "Guavio_Dam",  # Hydroelectric
        "Chivor_Dam": "Chivor_Dam",  # Hydroelectric
        "San_Carlos_Hydro": "San_Carlos_Hydroelectric_Power_Plant",  # Hydroelectric
        "Termocandelaria": "Termocandelaria_Power_Plant",  # Thermal
        "Tebsa_Power": "Tebsa_Power_Station",  # Thermal
        "Jepirachi_Wind": "Jepírachi_Wind_Farm",  # Wind
        "El_Quimbo": "El_Quimbo_Dam",  # Hydroelectric

        # Mexico
        "Chicoasen_Dam": "Chicoasén_Dam",  # Hydroelectric
        "Aguamilpa_Dam": "Aguamilpa_Dam",  # Hydroelectric
        "El_Cajon_Dam": "El_Cajón_Dam",  # Hydroelectric
        "La_Yesca_Dam": "La_Yesca_Dam",  # Hydroelectric
        "Laguna_Verde_Nuclear": "Laguna_Verde_Nuclear_Power_Station",  # Nuclear
        "Petacalco_Power": "Petacalco_Power_Station",  # Thermal
        "Tula_Power": "Tula_Power_Station",  # Thermal
        "Oaxaca_Wind_Farm": "Oaxaca_Wind_Farm",  # Wind
        "Don_Goyo_Solar": "Don_Goyo_Solar_Park",  # Solar

        # Peru
        "Cerro_del_Aguila": "Cerro_del_Águila_Dam",  # Hydroelectric
        "Chaglla_Dam": "Chaglla_Dam",  # Hydroelectric
        "Mantaro_Complex": "Mantaro_Hydroelectric_Complex",  # Hydroelectric
        "Chilca_Power": "Chilca_Power_Station",  # Thermal
        "Rubí_Solar": "Rubí_Solar_Power_Plant",  # Solar
        "Wayra_Wind": "Wayra_Wind_Farm",  # Wind

        # Venezuela
        "Guri_Dam": "Guri_Dam",  # Hydroelectric
        "Macagua_Dam": "Macagua_Dam",  # Hydroelectric
        "Caruachi_Dam": "Caruachi_Dam",  # Hydroelectric
        "Tocoma_Dam": "Tocoma_Dam",  # Hydroelectric
        "Planta_Centro": "Planta_Centro_Power_Station",  # Thermal

        # Paraguay
        "Acaray_Dam": "Acaray_Dam",  # Hydroelectric
        "Yguazu_Dam": "Yguazú_Dam",  # Hydroelectric

        # Ecuador
        "Coca_Codo_Sinclair": "Coca_Codo_Sinclair_Dam",  # Hydroelectric
        "Sopladora_Dam": "Sopladora_Dam",  # Hydroelectric
        "Minas_San_Francisco": "Minas_San_Francisco_Dam",  # Hydroelectric
        "Villonaco_Wind": "Villonaco_Wind_Power_Project",  # Wind

        # Uruguay
        "Baygorria_Dam": "Baygorria_Dam",  # Hydroelectric
        "Palmar_Dam": "Palmar_Dam",  # Hydroelectric
        "Rincon_del_Bonete": "Rincón_del_Bonete_Dam",  # Hydroelectric
        "Pampa_Wind": "Pampa_Wind_Farm",  # Wind
        "Valentines_Wind": "Valentines_Wind_Farm",  # Wind

        # Costa Rica
        "Reventazon_Dam": "Reventazón_Dam",  # Hydroelectric
        "Arenal_Dam": "Arenal_Dam",  # Hydroelectric
        "Miravalles_Geothermal": "Miravalles_Geothermal_Power_Plant",  # Geothermal

        # Panama
        "Fortuna_Dam": "Fortuna_Dam",  # Hydroelectric
        "Bayano_Dam": "Bayano_Dam",  # Hydroelectric
        "Chan_Dam": "Chan_Dam",  # Hydroelectric

        # Bolivia
        "San_Jacinto_Geothermal": "San_Jacinto_Geothermal_Power_Plant",  # Geothermal
        "Misicuni_Dam": "Misicuni_Dam",  # Hydroelectric
        "Qollpana_Wind": "Qollpana_Wind_Farm",  # Wind
    }
    
    # Initialize downloader with smaller max file size (500KB = 0.5MB)
    downloader = WikipediaImageDownloader()
    
    # Set up base directory for images
    base_directory = "power_plant_images"
    
    try:
        # Create folders and download images
        downloader.create_location_folders(base_directory, locations, images_per_location=70)
        print("\nDownload completed successfully!")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()