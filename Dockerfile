# Multi-stage Docker build for Keyword Intelligence Pipeline

# -------------------------
# Builder Stage
# -------------------------
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in a virtual env to copy easily
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install application in standard mode
COPY . .
RUN pip install --no-cache-dir .

# -------------------------
# Runtime Stage
# -------------------------
FROM python:3.11-slim

# Create a non-root user
RUN groupadd -r kipuser && useradd -r -g kipuser -m kipuser

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code for runtime
COPY keyword_intelligence ./keyword_intelligence
COPY VERSION .

# Ensure correct ownership
RUN chown -R kipuser:kipuser /app

# Switch to non-root user
USER kipuser

# Expose Streamlit port
EXPOSE 8501

# Add Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Start the application
CMD ["streamlit", "run", "keyword_intelligence/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
