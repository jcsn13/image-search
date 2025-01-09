FROM python:3.9-slim

# Install production dependencies
COPY . .
RUN pip install -r requirements.txt

# Copy local code to container image
WORKDIR /app

# Run the web service on container startup
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app