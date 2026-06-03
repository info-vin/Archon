name: "Phase 5.5.8 - Cloud Deployment & Monorepo Optimization SOP"
description: |
  Document the standardized deployment guidelines for Archon's monorepo architecture. Covers dual frontend hosting on Vercel with branch filtering to prevent unintended billing, and monolithic backend orchestration on Render leveraging container virtualization to run API, MCP, and Agent services together.

---

## Goal

**Feature Goal**: Standardize and document the cloud deployment procedures for the Archon monorepo. This prevents deployment conflicts, eliminates unexpected billing charges on Vercel due to automatic preview builds, and outlines the setup for Render's backend monolith (comprising the API, MCP, and Agent services in a single container).

**Deliverable**:
- `Phase_5.5.8_Cloud_Deployment_SOP.md` (this file) outlining steps, configurations, and verification processes.

**Success Definition**:
- Clear, reproducible steps for deploying both frontends to Vercel with branch locking.
- Clear, reproducible steps for deploying the consolidated backend monolith to Render.

---

## Why

- **Monorepo Complexity**: Having two frontends and a multi-service Python backend in a single repository requires precise configuration of root directories and build filters to avoid redundant compilation and high resource consumption.
- **Accidental Billing Protection**: Vercel's default Hobby behavior automatically builds every branch. If external database integrations (like Supabase Branching) are connected, switching Git branches triggers paid database provisions. Explicit branch isolation on Vercel prevents this loop.
- **Backend Resource Consolidation**: Running separate Render services for API, MCP, and Agents consumes multiple Free instances, increases communication latency, and hits limits. Packing them into a single container running via `start_all.sh` is efficient and cost-effective.

---

## Deployment SOP

### 1. Frontend Deployment (Vercel)

Both frontends (`archon-ui-main` and `enduser-ui-fe`) are hosted on Vercel. Because they exist in the same repository, they must be created as **two separate projects** in Vercel.

#### Step 1.1: Deploy Admin UI (`archon-ui-main`)
- **Vercel Project Name**: `archon-admin` (or custom)
- **Framework Preset**: `Vite`
- **Root Directory**: `archon-ui-main`
- **Environment Variables**:
  - Add `VITE_API_URL` pointing to your Render backend URL (e.g., `https://archon-backend.onrender.com`).
- **Git Branch Configuration (Settings > Git)**:
  - **Production Branch**: Set to `feat/twins` (or your active release branch).
  - **Ignored Build Step**: Set to **Custom** and enter:
    ```bash
    [ "$VERCEL_GIT_COMMIT_REF" != "feat/twins" ]
    ```
    *(This ensures Vercel only deploys when pushes are made to the `feat/twins` branch, ignoring `main`, `master`, or any other temporary branch to avoid unintended billing).*

#### Step 1.2: Deploy End-User UI (`enduser-ui-fe`)
- **Vercel Project Name**: `archon-enduser` (or custom)
- **Framework Preset**: `Vite`
- **Root Directory**: `enduser-ui-fe`
- **Environment Variables**:
  - Add `VITE_API_URL` pointing to your Render backend URL.
- **Git Branch Configuration (Settings > Git)**:
  - **Production Branch**: Set to `feat/twins`.
  - **Ignored Build Step**: Set to **Custom** and enter:
    ```bash
    [ "$VERCEL_GIT_COMMIT_REF" != "feat/twins" ]
    ```

---

### 2. Backend Monolith Deployment (Render)

The backend runs as a single monolithic Docker container on Render, launching the MCP server, Agents server, and main FastAPI app together using `start_all.sh`.

#### Step 2.1: Create Render Web Service
- **Type**: `Web Service`
- **Runtime**: `Docker`
- **Dockerfile Path**: `Dockerfile.server`
- **Docker Build Context Directory**: `.` (Project root directory)
- **Instance Type / Plan**: `Free`

#### Step 2.2: Set Health Check Path
- **Health Check Path**: `/api/health`
  *(FastAPI provides this endpoint to let Render check container health and manage traffic).*

#### Step 2.3: Set Build Filters (Recommended)
- **Included Paths**:
  - `python/**`
  - `Dockerfile.server`
  - `migration/**`
  *(This ensures Render only rebuilds the backend container when backend code changes, ignoring changes made to the frontend directories).*

#### Step 2.4: Environment Variables (Settings > Environment)
Configure these environment variables in your Render project:
- `SUPABASE_URL` = *(Your Supabase project URL)*
- `SUPABASE_SERVICE_KEY` = *(Your Supabase service_role key)*
- `GEMINI_API_KEY` = *(Your Gemini API key)*
- `OPENAI_API_KEY` = *(Your OpenAI API key, if applicable)*
- `ARCHON_SERVER_HOST` = `127.0.0.1`
- `ARCHON_SERVER_PORT` = `8181`
- `LOG_LEVEL` = `INFO`
- `CORS_ORIGINS` = `https://<your-admin-vercel-app>.vercel.app,https://<your-enduser-vercel-app>.vercel.app`
  *(Separate the two Vercel URLs with a comma. This permits the frontends to bypass CORS policies).*

---

### 3. Backend Monolith Deployment (Hugging Face Spaces - Recommended)

Hugging Face Spaces offers a highly generous free tier (2 vCPUs and 16GB of RAM), making it the recommended platform to run all backend services simultaneously without running out of memory.

#### Step 3.1: Create a Space on Hugging Face
- **SDK**: `Docker`
- **Template**: `Blank` (Do not select any template like FastAPI/Streamlit)
- **License**: `Apache 2.0` (or your choice)
- **Visibility**: `Public` (recommended so other services can access it) or `Private`.

#### Step 3.2: Configure Environment Secrets (Space Settings > Variables and Secrets)
Add the following key-value pairs under **Secrets** (similar to environment variables):
- `SUPABASE_URL` = `https://<your-project-id>.supabase.co`
- `SUPABASE_SERVICE_KEY` = *(Your Supabase service_role key)*
- `SUPABASE_DB_URL` = *(Your PostgreSQL connection string)*
- `GEMINI_API_KEY` = *(Your Gemini API key)*
- `OPENAI_API_KEY` = *(Your OpenAI API key, if applicable)*
- `CORS_ORIGINS` = `https://<your-admin-vercel-app>.vercel.app,https://<your-enduser-vercel-app>.vercel.app`
- `START_MCP` = `true` *(Optional, set true to run MCP tools)*
- `START_AGENTS` = `true` *(Optional, set true to run AI background agents)*

#### Step 3.3: Set Up Git Link & Build Link
Since Hugging Face Spaces builds automatically from its own repository, you need to push code to Hugging Face or link GitHub.

**Command Line Setup (Local workspace):**
1. Get a Write token from your Hugging Face settings: `https://huggingface.co/settings/tokens`.
2. Add Hugging Face as a Git remote in your terminal:
   ```bash
   git remote add hf https://<your-hf-username>:<your-write-token>@huggingface.co/spaces/<your-hf-username>/<your-space-name>
   ```
3. Create a symbolic link in the root folder so Hugging Face can locate the Dockerfile (Hugging Face expects the filename to be exactly `Dockerfile` in the root, whereas our file is named `Dockerfile.server`):
   ```bash
   ln -s Dockerfile.server Dockerfile
   git add Dockerfile
   git commit -m "chore: link Dockerfile.server to Dockerfile for Hugging Face"
   ```
4. Push your release branch (e.g. `feat/twins`) to Hugging Face's `main` branch:
   ```bash
   git push hf feat/twins:main --force
   ```

Hugging Face will automatically pull the Docker environment, build, and run it on port `7860`. The API URL to use in your Vercel frontend will be:
`https://<your-hf-username>-<your-space-name>.hf.space`

---

## Monolith Internals (`start_all.sh`)

When the Render container starts, it triggers the following launch sequence inside the container:

```bash
# 1. Starts MCP Server in the background (Default Port: 8051)
sh /app/docker-entrypoint-mcp.sh &

# 2. Starts Agents Service in the background (Default Port: 8052)
sh /app/docker-entrypoint-agents.sh &

# 3. Starts Main FastAPI Server in the foreground, binding to Render's dynamic $PORT
python -m uvicorn src.server.main:app --host 0.0.0.0 --port ${PORT:-8181} --workers 1
```

Services communicate internally via `localhost` (e.g., the FastAPI server routes requests to MCP via `localhost:8051`), providing an isolated, zero-cost network environment.
