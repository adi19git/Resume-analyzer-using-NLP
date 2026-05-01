FROM python:3.10-slim

# Prevent writing .pyc files and set output to unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (gcc and libpq-dev needed for psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data and Spacy model
RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('stopwords')"

# Copy application files
COPY backend /app/backend
COPY frontend /app/frontend

# Expose port
EXPOSE 8000

# Run Uvicorn from the backend directory
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
