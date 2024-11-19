# Use a lightweight official Python image as a parent image
FROM python:3.9-slim-buster

# Set environment variables to ensure that Python outputs everything in the container and doesn't buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

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

# Switch to non-root user
USER appuser

# Expose port 9099
EXPOSE 9099

# Run the application
CMD ["python", "app.py"]
