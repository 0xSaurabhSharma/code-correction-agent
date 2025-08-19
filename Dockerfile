# File: Dockerfile
# Stage 1: Build the wheel and install dependencies
FROM python:3.11-slim as builder

# Set the working directory in the container
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


# Stage 2: Create the final production image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the wheels from the builder stage and install them
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache-dir --no-deps /wheels/*

# Copy the rest of the application source code
COPY . .

# Expose the port the app will run on
EXPOSE 8080

# Command to run the application using Uvicorn
# We use an import string to run the app.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
