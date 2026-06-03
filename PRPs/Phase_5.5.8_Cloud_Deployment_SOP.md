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
  - Add `VITE_API_URL` pointing to your Render/Hugging Face backend URL.
  - Add `VITE_SUPABASE_URL` pointing to your Supabase URL (e.g. `https://<ref>.supabase.co`).
  - Add `VITE_SUPABASE_ANON_KEY` pointing to your Supabase public anon key (or service_role key).
- **Git Branch Configuration (Settings > Git)**:
  - **Production Branch**: Set to `feat/twins`.
  - **Ignored Build Step**: Set to **Custom** and enter:
    ```bash
    [ "$VERCEL_GIT_COMMIT_REF" != "feat/twins" ]
    ```---

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
3. Copy the Dockerfile to the root folder (Hugging Face expects the filename to be exactly `Dockerfile` in the root, whereas our template is named `Dockerfile.server`; **do not use symbolic links** as Hugging Face Spaces fails to resolve Git symlinks):
   ```bash
   cp Dockerfile.server Dockerfile
   git add Dockerfile
   git commit -m "chore: copy Dockerfile.server to Dockerfile for Hugging Face"
   ```
4. Push only the necessary backend files using a clean **orphan branch** to bypass Hugging Face's 10MB file limit hook and prevent git history bloat from UI assets/videos:
   ```bash
   # Create a clean orphan branch
   git checkout --orphan deploy-hf
   git rm -rf .
   
   # Restore only the required backend directories/files
   git checkout feat/twins -- python/
   git checkout feat/twins -- migration/
   git checkout feat/twins -- scripts/
   git checkout feat/twins -- Makefile
   git checkout feat/twins -- Dockerfile
   git checkout feat/twins -- Dockerfile.server

   # Create metadata README.md
   cat << 'EOF' > README.md
   ---
   title: Myrmidon
   emoji: 🐳
   colorFrom: blue
   colorTo: pink
   sdk: docker
   app_port: 8181
   pinned: false
   ---
   # Myrmidon Backend
   EOF

   git add python/ migration/ scripts/ Makefile Dockerfile Dockerfile.server README.md
   git commit -m "chore(deploy): build monolithic server"
   git push hf deploy-hf:main --force
   
   # Go back to your feature branch and delete temp deploy branch
   git checkout feat/twins
   git branch -D deploy-hf
   ```

Hugging Face will automatically pull the Docker environment, build, and run it on port `7860`. The API URL to use in your Vercel frontend will be:
`https://<your-hf-username>-<your-space-name>.hf.space`

---

## Monolith Internals (`start_all.sh`)

When the Render container starts, it triggers the following launch sequence inside the container:

```bash
# 1. Export local port parameters and host to ensure clean loopback routing inside monolith
export ARCHON_SERVER_PORT=${PORT:-8181}
export ARCHON_SERVER_HOST=${ARCHON_SERVER_HOST:-127.0.0.1}

# 2. Starts MCP Server in the background (Default Port: 8051)
PORT=$ARCHON_MCP_PORT sh /app/docker-entrypoint-mcp.sh &

# 3. Starts Agents Service in the background (Default Port: 8052)
PORT=$ARCHON_AGENTS_PORT sh /app/docker-entrypoint-agents.sh &

# 4. Starts Main FastAPI Server in the foreground, binding to the platform's dynamic $PORT
python -m uvicorn src.server.main:app --host 0.0.0.0 --port ${PORT:-8181} --workers 1
```

---

## Hugging Face Deployment Gotchas & Experiences (Added 2026-06-03)

1. **Pre-receive Hook Failures (File Size Limits)**:
   * *Problem*: Hugging Face Spaces rejects pushes containing files larger than 10MB (or matching test reports, `.webm` recordings, and build assets in frontend directories) even if they are in the historical commits.
   * *Solution*: Deploy using a clean `git checkout --orphan deploy-hf` branch containing zero commit history. Selectively check out only backend directories (`python/`, `migration/`, `scripts/`) to ensure the push remains minimal and under limits.
2. **Git Symbolic Link Resolution Failures**:
   * *Problem*: Creating `ln -s Dockerfile.server Dockerfile` results in Hugging Face cloning a literal text file containing the path text, causing the docker build to crash.
   * *Solution*: Physically copy the file using `cp Dockerfile.server Dockerfile`.
3. **Internal Container DNS Name Collisions (`Name or service not known`)**:
   * *Problem*: When running MCP, Agents, and Main FastAPI inside a single container (to bypass memory and billing constraints), Python's fallback address `"archon-server"` fails to resolve because there is no Compose-defined DNS.
   * *Solution*:
     * Modify client scripts to fallback to `127.0.0.1` or `localhost` when `ARCHON_SERVER_HOST` is unset.
     * Configure `start_all.sh` to dynamically bind `ARCHON_SERVER_PORT` to `${PORT:-8181}` so internal loopback communicates through the actual mapped routing port.
4. **Hugging Face Private Space 404/401 Routing Blocks**:
   * *Problem*: If the Hugging Face Space visibility is set to `Private`, Hugging Face's CDN intercepts all browser client-side JS requests (like Vercel frontend) that don't pass active Hugging Face authentication cookies, and returns `404 NOT FOUND` (or `401 Unauthorized`).
   * *Solution*: Change the Hugging Face Space visibility setting under Settings from `Private` to `Public` (Secrets and env keys remain completely encrypted and invisible to the public).
5. **Vercel Path Wildcard SPA Router 404s**:
   * *Problem*: React Router's URL refresh routing returns 404 on Vercel when using regex patterns in `vercel.json` like `/(.*)`.
   * *Solution*: Use standard Express-style wildcard route matcher `{ "source": "/:path*", "destination": "/index.html" }` in `vercel.json` to handle SPA route fallback properly.
6. **Required Supabase Credentials for Enduser Frontend**:
   * *Problem*: The enduser frontend (`enduser-ui-fe`) directly communicates with Supabase (via supabase-js SDK) to handle authentication, role authorization, and state mapping. In Vercel production, this fails if `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are not explicitly defined.
   * *Solution*: Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to Vercel environment variables for the enduser project.

