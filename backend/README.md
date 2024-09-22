# 🚀 Backend for SchemesSG V3

## 📚 Quick Navigation
- [Background](#background)
- [Getting Started](#getting-started)
- [Future Work](#future-work)

## Background

This backend is built using Firebase Functions and serves as the API for the SchemesSG V3 application. It currently includes two services: `/v1/chat` and `/v1/search`, which are coming soon. The boilerplates for the functions are already set up, with endpoints available for local testing:
- Chat Service: `/v1/chat` (coming soon)
- Search Service: `/v1/search` (coming soon)
- Test Endpoints: 
  - [Bar Service](http://127.0.0.1:5001/schemessg-v3-dev/us-central1/bar)
  - [Foo Service](http://127.0.0.1:5001/schemessg-v3-dev/us-central1/foo)

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

3. **Run the Cloud Functions Emulator**
   Start the emulator to test your functions locally:
   ```bash
   firebase emulators:start
   ```

4. **Access the endpoints**
   Once the emulator is running, you can issue HTTP requests to the endpoints:
   - Bar Service: [http://127.0.0.1:5001/schemessg-v3-dev/us-central1/bar](http://127.0.0.1:5001/schemessg-v3-dev/us-central1/bar)
   - Foo Service: [http://127.0.0.1:5001/schemessg-v3-dev/us-central1/foo](http://127.0.0.1:5001/schemessg-v3-dev/us-central1/foo)

## Future Work

- Refactor Fastapi into firebase functions, implement the `/v1/chat` and `/v1/search` functions.
- Use Firestore as database instead of local csv files.
- Set up production deployment configurations.
- Enhance error handling and logging for better debugging.
- Add unit tests for the functions to ensure reliability.