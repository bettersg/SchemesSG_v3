# 🚀 Backend for SchemesSG V3

## 📚 Quick Navigation
- [Background](#background)
- [Getting Started](#getting-started)
- [Future Work](#future-work)

## Background

This backend is built using Firebase Functions and serves as the API for the SchemesSG V3 application. The following endpoints are available for local testing:

- Health Check: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/health](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/health)
- Schemes Service: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes)
- Schemes Search: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search)
- Chat Message Service: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message)

Boilerplate Services (as a guide): 
- Bar Service: [https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/bar](https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/bar)
- Foo Service: [https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/foo](https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/foo)
- Main Service: [https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/main](https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/main)

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
   > 1. Press `Ctrl + Shift + P` (Windows/Linux) or `Cmd + Shift + P` (macOS)
   > 2. Search for "Docker: Attach Shell"
   > 3. Select the running container

4. **Access the endpoints**
   
   Local Mode 
   - Once the emulator is running, you can issue HTTP requests to the endpoints:
      - Health Check: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/health](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/health)
      - Schemes Service: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes)
      - Schemes Search: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search)
      - Chat Message Service: [http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message](http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message)
   
   Staging
   - These endpoints were deployed manually via `firebase deploy --only functions` in the schemessg-v3-dev project. All public users are able to access these endpoints temporarily. 
      - Bar Service: [https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/bar](https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/bar)
      - Foo Service: [https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/foo](https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/foo)
      - Main Service: [https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/main](https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/main)

## Future Work

- [X] Refactor Fastapi into firebase functions, implement the `/v1/chat` and `/v1/search` functions.
- [X] Use Firestore as database instead of local csv files.
- [X] Enhance error handling and logging for better debugging.
- [ ] Set up production deployment configurations.
- [ ] Add unit tests for the functions to ensure reliability.