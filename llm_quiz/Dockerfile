# Single unified image: builds the React Router frontend, then serves it plus the
# API from one FastAPI process. No uv, no virtualenv — pip installs directly into
# the image's system Python; the frontend is built with node + npm.
#
# Build:   docker build -t language-quiz .
# Run:     docker run -p 8070:8070 -e LLM_API_KEY=... language-quiz

# ---- Stage 1: build frontend (node + npm) -> emits backend/app/static/index.html + assets ----
# Use node (not bun): bun's `react-dom/server` resolves to `server.bun.js`, which lacks
# the `renderToPipeableStream` export that React Router's default server entry uses,
# so the SPA prerender 500s inside the bun runtime. node resolves it to `server.node.js`,
# which has the export.
FROM node:24-alpine AS frontend-build
WORKDIR /repo
COPY . .
WORKDIR /repo/frontend
RUN npm ci \
    && npm run build

# ---- Stage 2: FastAPI runtime (python), serves API + the static frontend ----
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend

# Backend source first, then overlay the frontend build produced in stage 1.
COPY backend/ /app/backend/
COPY --from=frontend-build /repo/backend/app/static/ /app/backend/app/static/

# Install into the image's system Python (no venv). Editable keeps the source
# layout; wheels for fastapi/sqlalchemy/openai/fugashi avoid build tools.
RUN pip install -e .

# Persist the SQLite DB (and llm_settings.json) in the container by default;
# override with -v on the host. The dir is created automatically by init_db.
VOLUME ["/app/backend/data"]

EXPOSE 8070
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8070"]