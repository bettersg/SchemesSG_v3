# Telegram Bot

To install and deploy, create a file called `.env` and place it in the `telegram_bot` folder.

```env
API_KEY=your-telegram-api-key
BACKEND_URL=your-backend-url
```

Enter the following commands (from `telegram_bot` folder)

```bash
# Installation
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Deployment
py app.py
```
