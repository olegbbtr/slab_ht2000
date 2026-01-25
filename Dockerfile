FROM python:3.13-slim

# Install system dependencies for HID and USB access
# libusb-1.0-0 for general USB
# libhidapi-hidraw0 / libhidapi-libusb0 for HIDAPI support
RUN apt-get update && apt-get install -y \
    libusb-1.0-0 \
    libhidapi-hidraw0 \
    libhidapi-libusb0 \
    udev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen: use uv.lock exactly
# --no-dev: do not install dev dependencies (if any)
RUN uv sync --frozen --no-dev

# Copy the source code
COPY src ./src

# Set the environment path to use the virtual environment created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "src/main.py"]
