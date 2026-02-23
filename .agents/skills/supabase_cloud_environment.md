---
description: Environment rules for Supabase Database interactions
---

# Supabase is Cloud-Native

## 🚨 CRITICAL RULE
**DO NOT use `docker exec`, `docker-compose exec`, or local `psql` commands to interact with the Supabase database.**

## Context
Archon uses a **Cloud-hosted Supabase instance**, NOT a local Docker-based database. 

## Prohibited Actions
- Never run: `docker exec -it supabase-db psql ...`
- Never run: `npx supabase status` or `npx supabase db ...` assuming a local instance.
- Never try to forcefully modify database schemas or permissions via local shell commands.

## Correct Procedures
1. **Schema Migrations**: If a schema change or permission grant is needed, you MUST write the SQL script and politely ask the USER to execute it in their Supabase Cloud SQL Editor.
2. **Migrations Directory**: Save the proposed SQL file in the `migration/` directory so the user can easily copy it.
3. **Data Verification**: To verify data, use the existing backend API logs (`archon-server`) or use the browser UI (`3737` or `5173`). Do not try to query the DB directly from the shell.
