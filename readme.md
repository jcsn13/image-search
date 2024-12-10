# Image Search with Gemini

This project uses Google Cloud's Gemini, Vertex AI Matching Engine, and Cloud Functions to create an image search application. Users upload images to a Cloud Storage bucket, which triggers a Cloud Function. The function processes the image with Gemini, generates an embedding, and stores it in a Vector Search index.

## Architecture

1. **Image Upload:** Users upload images to a Cloud Storage bucket designated for raw images.
2. **Cloud Function Trigger:** The image upload triggers a Cloud Function.
3. **Gemini Processing:** The Cloud Function uses the Gemini API to analyze the image, generating a textual description of its context, visual characteristics, and objects.
4. **Embedding Generation:**  A multimodal embedding is generated from the image and Gemini's analysis using Vertex AI's embedding model.
5. **Vector Search Storage:** The embedding and image metadata are stored in a Vertex AI Matching Engine index.
6. **Search (Future Implementation):**  A future component will allow users to search for similar images by providing a query image or text. This will query the Vector Search index for nearest neighbors based on embedding similarity.

## Deployment

This project uses Terraform to manage the infrastructure.

**Prerequisites:**

* **GCP Project:**  Create a GCP project and note its ID and number.
* **Service Account:** Create a service account with the necessary permissions (see IAM section).
* **gcloud CLI:** Install and configure the gcloud CLI.
* **Terraform:** Install Terraform.

**Steps:**

1. **Clone the repository:**   ```bash
   git clone https://github.com/your-username/your-repository.git   ```

2. **Navigate to the Terraform directory:**   ```bash
   cd terraform   ```

3. **Set environment variables:**   ```bash
   export GOOGLE_PROJECT=<your-project-id>
   export GOOGLE_REGION=<your-region>  # e.g., us-central1
   export GOOGLE_PROJECT_NUMBER=<your-project-number>   ```

4. **Initialize Terraform:**   ```bash
   terraform init   ```

5. **Plan and apply the Terraform configuration:**   ```bash
   terraform plan
   terraform apply   ```

## GCP Services and APIs

The following GCP services and APIs are used:

* **Cloud Storage:** For storing raw and processed images.
* **Cloud Functions:** For processing images and generating embeddings.
* **Gemini:** For analyzing image content.
* **Vertex AI:** For generating embeddings and managing the Vector Search index. Specifically:
    * **Vertex AI Matching Engine:** For storing and querying image embeddings.
    * **Vertex AI Multimodal Embedding Model:** For generating image and text embeddings.
* **Eventarc:** For triggering the Cloud Function based on Cloud Storage events.
* **Cloud Build:** For building the Cloud Function.

## Python Requirements

The Cloud Function requires the following Python packages:

```
google-cloud-storage>=2.0.0
google-cloud-aiplatform>=1.25.0
vertexai>=0.0.1
Pillow>=9.0.0
numpy>=1.21.0
functions-framework>=3.0.0
```


## IAM

The service account used by the Cloud Function requires the following roles:

* roles/bigquery.user
* roles/storage.objectAdmin
* roles/run.invoker
* roles/eventarc.eventReceiver
* roles/eventarc.serviceAgent
* roles/container.admin
* roles/resourcemanager.projectIamAdmin
* roles/compute.osLogin
* roles/vpcaccess.user
* roles/secretmanager.secretAccessor
* roles/aiplatform.user
* roles/cloudbuild.builds.builder
* roles/cloudfunctions.developer
* roles/iam.serviceAccountUser
* roles/run.developer
* roles/artifactregistry.reader
* roles/serviceusage.serviceUsageConsumer
* roles/logging.logWriter
* roles/cloudbuild.serviceAgent
* roles/pubsub.publisher

