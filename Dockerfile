# Use a lightweight Python image
FROM python:3.11-slim

# Update and install necessary system dependencies
RUN apt-get update && apt-get -y upgrade && apt-get install -y curl && apt-get clean

# Set environment variables
ENV \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.5.1

# Expose the FastAPI default port
EXPOSE 8000

# Set the working directory
WORKDIR /opt/geolocations

# Copy dependency files and install Poetry
COPY poetry.lock pyproject.toml ./
RUN pip install "poetry==$POETRY_VERSION"

# Export dependencies from Poetry and install them via pip
RUN poetry export --output requirements.txt --without-hashes
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Install `uvicorn` explicitly, if it's missing in the dependencies
RUN pip install uvicorn

# Copy the rest of the application code
COPY . .

# Define the command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]