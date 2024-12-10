# Preparação do Projeto Google Cloud para Deploy

Este documento detalha os requisitos e passos necessários para preparar um projeto Google Cloud para receber o deploy de uma aplicação que utiliza diversos serviços GCP, incluindo Vertex AI, Cloud Functions, Cloud Storage, e Cloud Build.

## 1. Habilitação de APIs

As seguintes APIs precisam ser habilitadas no projeto Google Cloud. O código Terraform presente em `main.tf` automatiza este processo, mas é importante garantir que a conta utilizada pelo Terraform tenha as permissões necessárias para tal ação.

**APIs Necessárias:**

*   **AI Platform (Vertex AI):** `aiplatform.googleapis.com`
*   **Cloud Functions:** `cloudfunctions.googleapis.com`
*   **Cloud Storage:** `storage.googleapis.com`
*   **Compute Engine:** `compute.googleapis.com`
*   **Container Registry:** `containerregistry.googleapis.com`
*   **Service Networking:**  `servicenetworking.googleapis.com`
*   **Vertex AI:** `vertexai.googleapis.com`

## 2. Configuração de Permissões IAM

O módulo IAM, definido em `modules/iam/main.tf`, configura as permissões necessárias para as contas de serviço utilizadas no projeto.

**Permissões Críticas:**

*   **Conta de Serviço Padrão:**
    *   `storage.objectAdmin`
    *   `aiplatform.user`
    *   `cloudfunctions.developer`
    *   `cloudbuild.builds.builder`
    *   *e outras permissões detalhadas em `modules/iam/main.tf`*

    É crucial revisar e ajustar essas permissões conforme as necessidades específicas do seu projeto e as políticas de segurança da sua organização.

## 3. Configuração da VPC Network

O módulo `vector_search` cria uma rede VPC dedicada para o Vertex AI Matching Engine. Esta etapa requer permissões para:

*   Criar e configurar redes VPC.
*   Gerenciar endereços IP globais.
*   Estabelecer conexões de peering.

## 4. Criação de Buckets do Cloud Storage

O projeto requer a criação dos seguintes buckets do Cloud Storage:

*   `raw_images`: Armazenamento das imagens brutas.
*   `processed_images`: Armazenamento das imagens processadas.
*   `function_bucket`: Armazenamento do código da Cloud Function.

A conta utilizada pelo Terraform deve ter permissões para criar e gerenciar buckets e seus objetos.

## 5. Configuração do Cloud Functions

O projeto utiliza Cloud Functions para o processamento de imagens, com as seguintes especificações:

*   **Runtime:** Python 3.9
*   **Dependências:** Definidas em `requirements.txt`
*   **Permissões:** Acesso aos buckets do Cloud Storage e ao índice do Vertex AI.

## 6. Configuração do Vertex AI

O projeto utiliza o Vertex AI Matching Engine para busca por similaridade e o Gemini para análise de imagens e geração de embeddings multimodais. As permissões necessárias incluem:

*   Criar e gerenciar índices, endpoints e deployments no Vertex AI.
*   Acessar e utilizar os modelos Gemini.

## 7. Definição de Organization Policies

O módulo `policy` configura diversas Organization Policies no nível do projeto. É importante:

*   Verificar se o projeto possui as permissões necessárias para modificar essas políticas.
*   Adaptar o código Terraform para remover ou modificar políticas que não se aplicam ao seu ambiente.

## 8. Configuração de Variáveis

As variáveis do projeto devem ser configuradas no arquivo `variables.tf`, incluindo:

*   `region`: Região do Google Cloud onde os recursos serão criados.
*   `project_id`: ID do projeto Google Cloud.
*   `project_number`: Número do projeto Google Cloud.

    **Atenção:** O `project_number` é crucial para a configuração de permissões IAM e deve ser verificado e inserido corretamente.

## 9. Configuração do Cloud Build

Um worker pool do Cloud Build é criado para construir e deployar a Cloud Function. A conta utilizada pelo Terraform deve ter permissões para:

*   Criar e gerenciar worker pools do Cloud Build.
*   Submeter e executar builds.

## Considerações Finais

Este projeto requer um ambiente Google Cloud bem configurado, com permissões adequadas para a criação e gerenciamento de recursos em diversos serviços. A utilização do Terraform facilita o processo de provisionamento e configuração, mas é fundamental revisar cuidadosamente todas as configurações e permissões para garantir a segurança e o bom funcionamento da aplicação. Recomenda-se adaptar as configurações e permissões conforme as políticas e restrições específicas do seu ambiente GCP.