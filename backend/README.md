# 🚀 Backend for SchemesSG V3

## 📚 Quick Navigation
- [Background](#background)
- [Getting Started](#getting-started)
- [Future Work](#future-work)

## Background

This backend is built using Firebase Functions and serves as the API for the SchemesSG V3 application. The following endpoints are available:

- Health Check (`health`)
- Schemes Service (`schemes`)
- Schemes Search (`schemes_search`)
- Chat Message Service (`chat_message`)
- Search Queries (`retrieve_search_queries`)
- Update Scheme (`update_scheme`)
- Feedback (`feedback`)

Additionally, there is a scheduled function that runs automatically:

- **Keep Endpoints Warm** (`keep_endpoints_warm`):
  - Type: Scheduled Function (runs every 4 minutes)
  - Purpose: Reduces cold starts by periodically warming up all endpoints
  - Memory: 1GB
  - Concurrency: 1 (only one instance at a time)
  - For local testing: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/keep_endpoints_warm-0](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/keep_endpoints_warm-0)
  - Note: The `-0` suffix is required for testing scheduled functions locally

## Getting Started

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Install Firebase CLI**

   Make sure you have Node.js installed, then install Firebase CLI globally:
   ```bash
   npm install -g firebase-tools
   ```

3. **Set up virtual environment**

   Make sure you have python 3.10 installed.
   
   > Note: These instructions are for Windows systems. For macOS/Linux users, you'll be using Docker instead (see next section).
   ```bash
   # Create a new virtual environment with Python 3.10
   python3.10 -m venv functions/venv

   # Activate the new virtual environment
   source functions/venv/bin/activate

   # Install the required packages
   python -m pip install -r functions/requirements.txt
   ```

3. **Run the Cloud Functions Emulator**

   Due to compatibility issues between Firebase Tools and macOS, we use Docker to provide a clean Linux environment for running the emulator.
   
   Before starting the emulator, ensure you have the following credential files:
   ```bash
   # Acquire the environment variables file and save it in
   backend/functions/.env

   # ACquire the Firebase credentials file and save it in 
   backend/functions/creds.json
   ```

   > Note: Contact the project maintainers to obtain the contents of these credential files.
   
   The setup uses Docker volume mounting to sync your local `functions/` directory with the container. This means any changes you make to your functions will automatically trigger a reload of the emulator.
   
   Start the emulator using Docker (make sure you're in the `backend/` directory):
   ```bash
   # Start the emulator
   docker compose -f docker-compose-firebase.yml up --build

   # To stop the emulator
   docker compose -f docker-compose-firebase.yml down

   # To attach to the running container's shell
   docker exec -it backend-backend-1 /bin/bash
   ```
    > Tip: Alternatively, you can attach to the running shell in VSCode by:
       1. Press `Ctrl + Shift + P` (Windows/Linux) or `Cmd + Shift + P` (macOS)
       2. Search for "Docker: Attach Shell"
       3. Select the running container


4. **Deploy to Staging Environment**

   To deploy functions to the staging environment (schemessg-v3-dev), use the following commands:
   Please do not deploy if you are not the project maintainers.
   ```bash
   # Navigate to backend directory
   cd backend

   # Deploy individual functions
   firebase deploy --only functions:health --debug
   firebase deploy --only functions:chat_message --debug
   firebase deploy --only functions:schemes_search --debug
   firebase deploy --only functions:schemes --debug
   firebase deploy --only functions:keep_endpoints_warm --debug  # Deploy the scheduled warmup function
   ```
   > Note: Make sure you have the necessary permissions and are logged in to the correct Firebase project before deploying.

4. **Access the endpoints**
   
   Local Mode 
   - Once the emulator is running, you can issue HTTP requests to the endpoints:
      - Health Check: `/health`
      - Schemes Service: `/schemes/{id}`
      - Schemes Search: `/schemes_search`
      - Chat Message Service: `/chat_message`
      - Search Queries: `/retrieve_search_queries/{session_id}`
      - Update Scheme: `/update_scheme`
      - Feedback: `/feedback`
   
   - Testing the scheduled warmup function locally:
      ```bash
      # Trigger the warmup function manually
      curl http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/keep_endpoints_warm-0
      
      # Check the Docker logs to see the warmup results
      docker compose -f docker-compose-firebase.yml logs -f functions
      ```
      > Note: The `-0` suffix is required when testing scheduled functions locally
   
   Staging
   - These endpoints were deployed manually via `firebase deploy --only functions` in the schemessg-v3-dev project. All public users are able to access these endpoints temporarily. Base URL: `https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net`
      - Health Check: `/health`
      - Schemes by ID: `/schemes/{id}`
      - Schemes Search: `/schemes_search`
      - Chat Message: `/chat_message`
      - Search Queries: `/retrieve_search_queries/{session_id}`
      - Update Scheme: `/update_scheme`
      - Feedback: `/feedback`
      > Note: The warmup function runs automatically in staging/production every 4 minutes

## Future Work

- [X] Refactor Fastapi into firebase functions, implement the `/v1/chat` and `/v1/search` functions.
- [X] Use Firestore as database instead of local csv files.
- [X] Enhance error handling and logging for better debugging.
- [ ] Set up production deployment configurations.
- [ ] Add unit tests for the functions to ensure reliability.