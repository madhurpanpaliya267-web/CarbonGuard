# Deployment Guide

This guide covers deploying CarbonGuard using Docker.

## Docker Setup

### Prerequisites

- Docker 20.10+
- Docker Compose v2+

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd CarbonGuard

# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost | React application (nginx) |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |

## Docker Configuration

### Backend Dockerfile

- **Base**: `python:3.12-slim`
- **Dependencies**: Installed from `requirements.txt`
- **Port**: 8000
- **Healthcheck**: HTTP GET `/health` every 30s
- **Data persistence**: Named volume `backend-data` at `/app/data`

### Frontend Dockerfile

- **Build stage**: `node:20-alpine` — runs `npm ci` + `npm run build`
- **Serve stage**: `nginx:alpine` — serves static files
- **Port**: 80
- **Reverse proxy**: `/api/` requests forwarded to `http://backend:8000`
- **SPA fallback**: All routes serve `index.html`

### nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### docker-compose.yml

Two services:
- `backend` — Python/FastAPI with SQLite persistence
- `frontend` — nginx with API reverse proxy

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["backend-data:/app/data"]
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s

  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on:
      backend:
        condition: service_healthy
```

## Environment Configuration

Environment variables are passed to containers via `docker-compose.yml`. To override:

1. Create a `docker-compose.override.yml`:
```yaml
services:
  backend:
    environment:
      - DEBUG=true
      - DEFAULT_CARBON_INTENSITY=500
```

2. Or export variables before running:
```bash
export DEFAULT_CARBON_INTENSITY=500
docker compose up -d
```

## Data Persistence

The SQLite database is stored in a Docker named volume `backend-data` mounted at `/app/data`. To backup:

```bash
# Copy database out of container
docker cp carbon-guard-backend:/app/data/carbon_guard.db ./backup.db

# Restore
docker cp ./backup.db carbon-guard-backend:/app/data/carbon_guard.db
docker compose restart backend
```

## Production Considerations

### Security

- **Never** use default `.env` values in production
- Set `DEBUG=false`
- Use a production-grade database (PostgreSQL) instead of SQLite
- Add TLS termination via reverse proxy (Caddy, Traefik, nginx)

### Performance

- The frontend bundle is ~744KB (from Recharts). Consider code splitting for production.
- SQLite is suitable for development and small deployments. For larger scale, migrate to PostgreSQL.

### Scaling

The current architecture supports single-instance deployment. For horizontal scaling:
- Replace SQLite with PostgreSQL
- Add session/state management
- Use a message queue for async tasks

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push to `main`/`develop`:

| Job | Steps |
|-----|-------|
| `backend-tests` | Python 3.12 → pip install → pytest |
| `frontend-checks` | Node 20 → npm ci → tsc --noEmit → npm run build |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check `DATABASE_URL` in `.env`, ensure port 8000 is free |
| Frontend can't reach API | Verify backend is running, check `CORS_ORIGINS` |
| Docker build fails | Ensure Docker daemon is running, check disk space |
| Database errors | Delete `carbon_guard.db` and restart (or re-seed) |
