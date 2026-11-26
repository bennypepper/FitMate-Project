FROM python:3.11-slim

# Creates directory and sets it as the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend files into the container
COPY . .

# Run as non-root user (compatible with Hugging Face Spaces UID 1000)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Hugging Face Spaces expose port 7860 by default
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/health', timeout=3)" || exit 1

# Command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
