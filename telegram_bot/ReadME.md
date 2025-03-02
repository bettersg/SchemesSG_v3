# Telegram Bot

To install and deploy, create a file called `.env` and place it in the `telegram_bot` folder, as seen in `.env.sample`. Add the Firebase credentials file into the `telegram_bot` folder as well (set `FB_CREDS_PATH` to the file path).

```env
API_KEY=your-telegram-api-key
BACKEND_URL=your-backend-url
FB_API_KEY=firebase-api-key
FB_CREDS_PATH=path-to-firebase-credentials
```

### Development

Enter the following commands (from `telegram_bot` folder)

```bash
# Installation
deactivate
poetry install
poetry run python app.py

# Deployment
poetry run python app.py
```

### Production

Run the `deploy.sh` shell script on your server console from this (`telegram_bot`) directory.
