#!/bin/bash

# Exit on error
set -e

# Configuration variables - replace these with your values
PROJECT_ID="your-project-id"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prompt for service account name with default value
echo -e "${BLUE}Enter service account name (press Enter for 'default-sa'):${NC}"
read SA_NAME
SA_NAME=${SA_NAME:-"default-sa"}

echo -e "${GREEN}1. Setting up Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

echo -e "${GREEN}2. Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com

echo -e "${GREEN}3. Creating and downloading service account key...${NC}"
# Generate new key
gcloud iam service-accounts keys create key.json \
    --iam-account=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

echo -e "${GREEN}4. Creating Secret Manager secret from key.json...${NC}"
# Create secret
gcloud secrets create service-account-key \
    --data-file=key.json \
    --replication-policy="automatic"

echo -e "${GREEN}5. Granting Secret Manager access to service account...${NC}"
gcloud secrets add-iam-policy-binding service-account-key \
    --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo -e "${GREEN}6. Cleaning up local key file...${NC}"
rm key.json

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Remember: When deploying to Cloud Run, use:${NC}"
echo -e "${GREEN}--set-secrets=/app/secrets/key.json=service-account-key:latest${NC}" 