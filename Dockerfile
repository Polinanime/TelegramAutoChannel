FROM python:3.9-alpine

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev


# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data tmp

# Run the application
CMD ["python", "main.py"]
