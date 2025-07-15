# Stage 1: React build
FROM node:20 AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN ls -l /frontend          # List files before build!
RUN npm run build
RUN ls -l /frontend/dist    # List files after build!

# Stage 2: FastAPI backend
FROM python:3.11-slim AS backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY latest_version.txt /app/latest_version.txt 
COPY --from=frontend-builder /frontend/dist /app/frontend_build
RUN echo "Listing /app/frontend_build:" && ls -l /app/frontend_build




CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
