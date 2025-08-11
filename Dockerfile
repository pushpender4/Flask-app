# # Use Python image
# FROM python:3.10-slim

# # Set work directory
# WORKDIR /app

# # Copy files
# COPY . .

# # Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Run app
# CMD ["python", "app/main.py"]
# ---------------------
# Stage 1: Build stage
# ---------------------
FROM python:3.10-slim AS builder

# Set work directory
WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ---------------------
# Stage 2: Runtime stage
# ---------------------
FROM python:3.10-slim

WORKDIR /app

# Install only needed runtime dependencies (from builder)
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Update PATH so Python finds installed packages
ENV PATH=/root/.local/bin:$PATH

# Run the application
CMD ["python", "-m", "app.main"]
