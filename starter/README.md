# Starter

A Flask API and a React + TypeScript UI to start the tax calculator from. Use it or bring your own stack.

The UI only talks to the Python API. The Python API is the one that calls the tax brackets service at `https://{app-name}.fly.dev`. The app name is provided during the interview call.

```
React UI  ──/api──▶  Python API  ──▶  {app-name}.fly.dev
```

Run the backend first, then the frontend.

## Backend (Python 3.10+)

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export TAX_API_URL=https://{app-name}.fly.dev
flask --app tax_calculator run --debug --port 8000
pytest
ruff check . && ruff format .
```

Layout: `tax_calculator/` holds the app factory (`create_app`), config from env (`TAX_API_URL` required, `LOG_LEVEL`) and the `/api` blueprint. Tests live in `tests/`.

## Frontend (Node 20+)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, /api is proxied to the backend
```
