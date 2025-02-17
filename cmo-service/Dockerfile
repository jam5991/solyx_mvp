FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install DRM Core as a dependency
RUN pip install drm-core

COPY src/ ./src/

ENV PORT=8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "${PORT}"] 