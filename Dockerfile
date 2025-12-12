# Set base image to use
FROM python:3.9-slim

# Set up the Python development environment
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Upgrade pip and install requirements
RUN python3 -m pip install --upgrade pip wheel
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy remaining files
COPY service/ ./service

# Set a non-root user for security purposes
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

# Expose ports
EXPOSE 8080

# Run the service
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]

# Labeling the image
LABEL version="1.0"
LABEL description="Account Docker image"
LABEL maintainer="talia"

# Healthcheck to ensure the container is running correctly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -fs http://localhost:$PORT || exit 1



