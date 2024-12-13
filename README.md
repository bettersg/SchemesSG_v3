# Schemes Reimagined

**Schemesv3** is a modern reimagining of Singapore's social support system search, built using Firebase Cloud Functions and Next.js. The system leverages Azure OpenAI's GPT models to provide intelligent scheme recommendations and natural language interactions.

The core functionality is powered by a sophisticated search system that combines:
- **Natural Language Search**: Users can describe their situation in everyday language and receive relevant scheme recommendations
- **Intelligent Chat Interface**: Contextual conversations powered by Azure OpenAI to help users understand scheme eligibility and application processes
- **Vector-Based Scheme Matching**: FAISS similarity search to match user situations with the most relevant support schemes
- **Serverless Architecture**: Firebase Cloud Functions with Python runtime for scalable, maintainable backend operations
- **Modern Web Interface**: Responsive Next.js frontend with TypeScript for a seamless user experience

## Prerequisites

Ensure you have the following installed:
- **Node.js** (v14 or later): [Download Node.js](https://nodejs.org/)
- **npm** (v6 or later): Comes with Node.js
- **Python** (v3.10): [Download Python](https://www.python.org/downloads/)
- **Firebase CLI**: Install globally using `npm install -g firebase-tools`
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Included with Docker Desktop

### Required Files Setup

1. **Environment Variables**
Create `.env` file in `backend/functions/`:
```shell
APIKEY= # Azure OpenAI key
TYPE= # Azure OpenAI type, e.g. "xxxx-Preview"
VERSION= # Azure OpenAI version, e.g. "2022-02-16-preview"
ENDPOINT= # Azure endpoint, e.g. "https://example-resource.azure.openai.com/"
DEPLOYMENT= # Azure OpenAI model deployment
MODEL= # Azure OpenAI model name, e.g. "gpt-4"
```

2. **Model Files**
Download and place the following files in `backend/functions/ml_logic/`:
- `schemesv2-torch-allmpp-model/`
- `schemesv2-torch-allmpp-tokenizer/`
- Required `.npy` files
- Required `.faiss` files

You can obtain these files from:
- Google Drive (contact maintainers for access) or
- Build them yourself using `model-creation-transformer-faiss.ipynb`

## Project Structure

The project consists of two main components:

1. **Frontend**: Next.js application with TypeScript
   - See `frontend/README.md` for setup instructions
   - Staging URL: https://schemessg-v3-dev.web.app/

2. **Backend**: Firebase Functions with Python 3.10 runtime
   - See `backend/README.md` for setup instructions
   - Staging URL: https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/

## Development Workflow

1. Frontend changes:
   - Branch from `stg`
   - Make changes
   - Test locally
   - Create PR to `stg`

2. Backend changes:
   - Test using Firebase emulator
   - Deploy to staging only if you're a project maintainer

## Notes
- Production deployment is not yet configured
- For any issues, contact Traci on Slack or WhatsApp