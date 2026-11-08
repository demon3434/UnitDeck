# Python Backend Runtime & Frontend Static Host
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    PORT=8080

# Configure Aliyun Debian Mirror for rock-solid stability and high speed
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null

# Install system utilities needed for systemctl & dbus communication
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    curl \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies (using Aliyun PyPI mirror)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# Copy backend application
COPY backend/app ./app

# Copy built frontend assets
COPY frontend/dist ./frontend/dist

EXPOSE 8080

VOLUME ["/app/data"]

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
