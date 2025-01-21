gcloud run deploy image-search-ui \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets=/app/secrets/key.json=service-account-key:latest