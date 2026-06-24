# --- Stage 1: Build dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies if needed, and compile requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Final runtime image ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/requirements.txt .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy project files
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit dashboard
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
