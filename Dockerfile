FROM python:3.12-slim AS backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn
COPY backend/ .
RUN mkdir -p data
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:20-slim AS frontend-build
WORKDIR /app
COPY frontend-redesigned/package*.json ./
RUN npm ci --prefer-offline 2>/dev/null || npm install
COPY frontend-redesigned/ .
RUN npm run build

FROM nginx:alpine AS frontend
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
