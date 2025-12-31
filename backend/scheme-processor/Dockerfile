FROM python:3.11-slim

# Install system dependencies for Playwright and Pydoll
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates fonts-liberation curl \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libxcomposite1 libxdamage1 libxfixes3 \
    libxkbcommon0 libxrandr2 xdg-utils \
    # Xvfb for Pydoll virtual display (Cloudflare bypass)
    xvfb \
    # Chromium for Pydoll
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome path for Pydoll
ENV CHROME_PATH=/usr/bin/chromium

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files for dependency installation
COPY pyproject.toml uv.lock* ./

# Install dependencies with uv (create venv in project)
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Install Playwright browsers
RUN uv run playwright install chromium --with-deps

# Copy application code
COPY app/ ./app/

ENV PORT=8081
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
