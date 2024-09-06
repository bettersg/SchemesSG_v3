# Telegram Bot

To install and deploy, create a file called `.env` and place it in the `telegram_bot` folder, as seen in `.env.sample`.

```env
API_KEY=your-telegram-api-key
BACKEND_URL=your-backend-url
```

Enter the following commands (from `telegram_bot` folder)

```bash
# Installation
deactivate
poetry install
poetry run python app.py

# Deployment
python app.py
```

### Progress

[x] Implement schemes recommendation
[x] Implement chatbot integration
[ ] Better data storage (with SQLite/MongoDB/Other databases; currently stored in json files)