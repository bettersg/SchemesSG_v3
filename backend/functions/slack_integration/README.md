# Slack integration

This folder implements the Slack review workflow and exposes 3 Firebase HTTP functions:
- `slack_trigger_message` — manual POST to post a scheme for review
- `slack_scan_and_notify` — batch scanner to post new schemes needing review
- `slack_interactive` — Slack interactive endpoint: opens modal and handles submissions

Purpose
- Post scraped schemes into a Slack channel for human review.
- Allow reviewer to click "Review" in Slack, open a modal, edit details and save back to Firestore.

Prerequisites
- Firebase project & Firestore (dev emulator or real project)
- Slack app with:
  - Bot token (Bot User OAuth Token)
  - Signing secret
  - Interactive components enabled (Request URL)
  - Appropriate OAuth scopes (chat:write, commands, im:write, users:read, channels:read, channels:join, views:write — adjust as needed)
- Local dev tools: Docker (optional), firebase-tools (for emulator), ngrok (for exposing local endpoint to Slack)

Local run / test (quick)
### 1) Copy env file with additional slack credentials
Additional credentials: 
- SLACK_BOT_TOKEN (xoxb-...)
  - SLACK_SIGNING_SECRET
  - SLACK_CHANNEL_ID (channel to post messages)
  - Firebase credentials or emulator vars as needed

### 2) Start Firebase emulator 

### 3) Set up ngrok
Slack needs to reach `slack_interactive` over HTTPS. Use ngrok to create a secure public tunnel that forwards traffic to your local Firebase Functions emulator.

1. Install and set up ngrok (macOS)
- Homebrew: https://ngrok.com/download/mac-os 
2. Start ngrok tunnel to port 5001
Basic tunnel:
```bash
ngrok http 5001
```
ngrok output will show two public URLs (http and https). Copy the https URL (e.g. https://abcd-1234.ngrok-free.dev).

### 4) Configure your Slack App -> Interactive Components
- In the Slack App admin page → Interactivity & Shortcuts → Request URL
- Set the Request URL to:
  https://<NGROK_HOST>/schemessg-v3-dev/asia-southeast1/slack_interactive
- For Example, this is my ngrok url: 
  https://relievedly-lepidopterous-georgine.ngrok-free.dev
- And so, my Request URL is https://relievedly-lepidopterous-georgine.ngrok-free.dev/schemessg-v3-dev/asia-southeast1/slack_interactive 
- Save changes. Slack will send a verification request; your emulator must be reachable and return 200.

### 5) end-to-end manual test (once tunnel + emulator are running)
Post a manual trigger to create a review message:
```bash
curl -X POST http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/slack_trigger_message \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test-scheme-full",
    "scheme_name": "18decrun_Healthcare Assistance Program",
    "scheme_url": "https://example.com/healthcare-program",
    "channel": "C09LTH8E1KQ",
    "agency": "Ministry of Health",
    "image_url": "https://example.com/scheme-image.jpg",
    "phone": "+65 1234 5678",
    "address": "123 Health Street, Singapore 123456",
    "who_is_it_for": "seniors",
    "what_it_gives": "healthcare_support",
    "scheme_type": "healthcare",
    "llm_description": "This program provides comprehensive healthcare assistance for senior citizens, including medical consultations, medication subsidies, and health screening services.",
    "eligibility": "Singapore citizens aged 65 and above with household income below $3000 per month",
    "how_to_apply": "Apply online through the Health Assist portal or visit any Community Centre with required documents (NRIC, income statements, medical reports)"
  }'
```

In Slack, click the Review button on the posted message — it should open a modal that posts back to the same Request URL and be processed by your function.

