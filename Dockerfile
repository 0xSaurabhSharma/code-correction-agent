# Dockerfile (updated for your project structure)
# - two-stage build: build wheels in builder, install in final image
# - defaults PORT=8080 (Cloud Run friendly), but you can override it
# - copies entire repo into /app (keeps templates/, app/, main.py, etc)

# -----------------------
# Stage 1: build wheels
# -----------------------
    FROM python:3.11-slim AS builder

    ENV PYTHONUNBUFFERED=1 \
        PIP_NO_CACHE_DIR=1
    
    WORKDIR /app
    
    # Install build tools required for many Python packages
    RUN apt-get update \
        && apt-get install --no-install-recommends -y \
           build-essential \
           gcc \
           git \
           libffi-dev \
           libssl-dev \
           make \
        && rm -rf /var/lib/apt/lists/*
    
    # Copy only requirements first to leverage Docker cache
    COPY requirements.txt /app/requirements.txt
    
    # Build wheels into /wheels (faster subsequent installs)
    RUN python -m pip install --upgrade pip setuptools wheel \
     && pip wheel --no-cache-dir --wheel-dir /wheels -r /app/requirements.txt
    
    # -----------------------
    # Stage 2: runtime image
    # -----------------------
    FROM python:3.11-slim
    
    ENV PYTHONUNBUFFERED=1 \
        PIP_NO_CACHE_DIR=1 \
        PORT=8080
    
    WORKDIR /app
    
    # (Optional) install runtime system deps if any are needed at runtime.
    # Add packages if your app needs them (e.g. libpq5 for psycopg2 runtime)
    RUN apt-get update \
      && apt-get install --no-install-recommends -y ca-certificates \
      && rm -rf /var/lib/apt/lists/*
    
    # Copy pre-built wheels and requirements file from builder
    COPY --from=builder /wheels /wheels
    COPY --from=builder /app/requirements.txt /app/requirements.txt
    
    # Install wheels (no network access required at this step)
    RUN pip install --no-cache-dir /wheels/*
    
    # Copy application code (templates/, app/, main.py, etc)
    COPY . /app
    
    # Expose default port (Cloud Run uses 8080 by convention)
    EXPOSE 8080
    
    # Use sh -c so we can expand ${PORT} environment variable at runtime.
    # Production: remove --reload and consider adding --workers N
    CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
    