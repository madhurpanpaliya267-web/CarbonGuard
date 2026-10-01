# Carbon Guard - Development Guidelines

## Project Rules

1. **SIMULATED DATA ONLY**: All security events, attacks, and monitoring data are simulated/synthetic. Never perform real cyber attacks, scan real systems, or generate real malware.

2. **LABEL SIMULATED DATA**: Always clearly label simulated/demo data wherever it appears in the UI or API responses.

3. **SECURITY FIRST**: Security tasks are NEVER delayed or degraded for carbon optimization. Critical security workloads take absolute priority.

4. **ESTIMATED vs MEASURED**: Clearly distinguish estimated/simulated data from measured data. When physical energy measurements are unavailable, use estimation models and label them as such.

## Architecture Principles

### Backend (Python + FastAPI)
- **Thin Routes**: API routes parse requests and call services. No business logic in routes.
- **Service Layer**: Business logic, validation, orchestration lives here.
- **Engine Layer**: Domain-specific computation (security, carbon, optimizer, AI).
- **Repository Layer**: Database CRUD operations only.
- **No Circular Dependencies**: `main` → `api` → `services` → `repositories` → `models`.

### Frontend (React + TypeScript)
- **Feature-Based Organization**: Group code by domain (dashboard, security, carbon, etc.).
- **Shared Components**: Reusable UI primitives in `shared/ui/`.
- **API Layer**: All API calls go through `shared/utils/apiClient.ts`.
- **Type Safety**: Strict TypeScript, no `any` types.

## File Naming Conventions

### Backend
- Models: `snake_case.py` in `app/models/`
- Schemas: `snake_case.py` in `app/schemas/`
- Services: `snake_case_service.py` in `app/services/`
- Engines: Module folders in `app/engines/`
- Repos: `snake_case_repo.py` in `app/repositories/`
- API Routes: `snake_case.py` in `app/api/`

### Frontend
- Components: `PascalCase.tsx` in feature `components/` folders
- Hooks: `use*.ts` in feature `hooks/` folders
- Types: `camelCase.ts` in feature `types/` folders
- Utilities: `camelCase.ts` in `shared/utils/`

## Development Workflow

1. Understand the existing code patterns before making changes
2. Follow the established architecture (thin routes, service layer, engine layer)
3. Use shared UI components from `shared/ui/`
4. Add proper TypeScript types for all API responses
5. Test API endpoints before connecting frontend
6. Run lint and typecheck before committing

## Key Carbon Calculation Formulas

```
Energy Consumption (kWh) × Carbon Intensity (gCO2/kWh) = Gross CO2 (gCO2)
Gross CO2 × (Renewable % / 100) = Renewable Offset (gCO2)
Gross CO2 - Renewable Offset = Net CO2 (gCO2)
```

## Workload Optimization Rules

1. Critical security tasks are NEVER delayed for carbon savings
2. Non-critical tasks may be shifted to lower-carbon periods
3. Shift window is limited (max 4 hours delay by default)
4. Minimum savings threshold must be met to justify shifting
5. Always show BEFORE vs AFTER comparison

## Running Tests

### Backend
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm run build
```

## Environment Configuration

- Backend: `backend/.env` (copy from `.env.example`)
- Frontend: `frontend/.env` (copy from `.env.example`)

Never commit `.env` files to version control.
