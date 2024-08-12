# Use a lightweight official Python image as a parent image
FROM python:3.9-slim-buster

# Set environment variables to ensure that Python outputs everything in the container and doesn't buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    KMP_DUPLICATE_LIB_OK=TRUE

# Install Poetry and create a non-root user
RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s $HOME/.local/bin/poetry /usr/local/bin/poetry \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser

# Set the working directory
WORKDIR /app

# Copy only the necessary files to install dependencies
COPY --chown=appuser:appuser pyproject.toml poetry.lock /app/

# Install production dependencies only
RUN poetry install --only main --no-root

# Copy the rest of the application code and set ownership to the non-root user
COPY --chown=appuser:appuser . /app

# Download the spaCy model
RUN python -m spacy download en_core_web_sm

# Switch to non-root user
USER appuser

# Expose the port (optional: you can set the port via an environment variable)
EXPOSE $PORT

# Run the application with Uvicorn using shell form to expand environment variables
CMD uvicorn fast_api.api:app --host 0.0.0.0 --port ${PORT:-8000}
