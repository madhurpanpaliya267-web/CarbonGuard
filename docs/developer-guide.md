# Developer Guide

This guide covers setting up the CarbonGuard development environment from scratch.

## Prerequisites

- **Python** 3.12+
- **Node.js** 20+ and npm
- **Git**

## Project Structure

```
CarbonGuard/
├── backend/                # Python FastAPI backend
│   ├── app/               # Application source code
│   │   ├── api/           # API route handlers
│   │   ├── services/      # Business logic
│   │   ├── engines/       # Domain computation
│   │   ├── repositories/  # Database CRUD
│   │   ├── models/        # ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── config.py      # Settings
│   │   ├── database.py    # DB connection
│   │   └── main.py        # FastAPI app
│   ├── tests/             # Test suite
│   ├── seed.py            # Database seeder
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment template
├── frontend/              # React TypeScript frontend
│   ├── src/               # Source code
│   │   ├── features/      # Feature modules (13)
│   │   ├── shared/        # Shared components, utils, types
│   │   ├── App.tsx        # Router
│   │   └── main.tsx       # Entry point
│   ├── package.json       # Node dependencies
│   └── .env.example       # Environment template
├── docs/                  # Documentation
├── docker-compose.yml     # Docker orchestration
└── .github/workflows/     # CI/CD
```

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend

# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

The `.env` file contains:
```env
APP_NAME=Carbon Guard
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./carbon_guard.db
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
DEFAULT_CARBON_INTENSITY=475
DEFAULT_RENEWABLE_PERCENTAGE=25
DEFAULT_ENERGY_CONSUMPTION_KWH=0.5
MINIMUM_SAVINGS_THRESHOLD=0.01
MAX_DELAY_HOURS=4
```

### 4. Seed Database (Optional)

```bash
python seed.py
```

This populates the database with demo data for all 8 tables.

### 5. Start Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

Backend available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment (Optional)

```bash
cp .env.example .env
```

Default API URL: `http://localhost:8000/api/v1`
The Vite dev server proxies `/api` requests to the backend automatically.

### 3. Start Frontend Dev Server

```bash
npm run dev
```

Frontend available at: `http://localhost:5173`

## Running Tests

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

This runs **187 tests** across:
- 46 API integration tests (13 route modules)
- 64 engine unit tests (8 engine modules)
- 77 service unit tests (9 service classes)

### Frontend Tests

```bash
cd frontend
npm test
```

This runs **187 tests** across:
- 13 page tests (one per feature)
- 14 shared UI component tests
- 1 layout test
- 1 utility test
- 1 routing test

### Frontend Type Check

```bash
cd frontend
npx tsc --noEmit
```

### Frontend Production Build

```bash
cd frontend
npm run build
```

Output: `frontend/dist/`

## Development Workflow

1. **Understand existing patterns** before making changes
2. **Follow the layered architecture** (routes → services → engines/repos)
3. **Use shared UI components** from `src/shared/ui/`
4. **Add TypeScript types** for all API responses
5. **Write tests** for new features
6. **Run lint and typecheck** before committing

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Carbon Guard | Application name |
| `APP_VERSION` | 1.0.0 | Application version |
| `DEBUG` | true | Enable debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `DATABASE_URL` | sqlite:///./carbon_guard.db | Database connection string |
| `CORS_ORIGINS` | ["http://localhost:5173"] | Allowed CORS origins |
| `DEFAULT_CARBON_INTENSITY` | 475 | gCO2/kWh default |
| `DEFAULT_RENEWABLE_PERCENTAGE` | 25 | Renewable energy % default |
| `DEFAULT_ENERGY_CONSUMPTION_KWH` | 0.5 | Default energy consumption |
| `MINIMUM_SAVINGS_THRESHOLD` | 0.01 | Min savings to justify shifting |
| `MAX_DELAY_HOURS` | 4 | Max workload delay |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | http://localhost:8000/api/v1 | Backend API URL |

## Code Style

### Python
- Follow PEP 8
- Use type hints
- snake_case for functions and variables
- PascalCase for classes

### TypeScript
- Strict TypeScript mode (no `any`)
- PascalCase for components and types
- camelCase for functions and variables
- Use shared types from `src/shared/types/`

## Important Notes

- **Simulated data only**: All security events, attacks, and monitoring data are synthetic
- **Label simulated data**: Always label demo data in UI and API responses
- **Security first**: Critical security tasks are never delayed for carbon optimization
- **Estimated vs measured**: Clearly distinguish estimated values from measured data
