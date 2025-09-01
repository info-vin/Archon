# End User UI Frontend

This project is the user-facing frontend for the Archon Task Management system. It is built with React, Vite, and TypeScript.

## Development Setup

To run this project locally for development, please follow these steps.

### 1. Install Dependencies
Navigate to this directory and install the required packages.
```bash
npm install
```

### 2. Environment Configuration
This project connects to a Supabase backend. You will need to get the connection details from the main project setup.

1.  In the project root, copy the example environment file:
    ```bash
    # Run this from the project's root directory
    cp .env.example .env
    ```
2.  Open the newly created `.env` file and fill in your `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`. The frontend will not function correctly without these.

### 3. Database Setup (Crucial for Development)
For a fully functional development environment with test data, you must set up and seed your Supabase database.

In your Supabase project's SQL Editor:

1.  **Create Schema**: First, run the contents of `migration/complete_setup.sql` to create all the necessary tables and database structure.
2.  **Seed Data**: Immediately after, run the contents of `migration/seed_mock_data.sql` to fill the tables with initial test projects, users, and tasks.

### 4. Running the Development Server
Once the setup is complete, you can start the Vite development server.
```bash
npm run dev
```
The application should now be running on `http://localhost:5173` by default.

**Note on Ports:** `5173` is the default port for the local Vite development server. If you are running the entire Archon project via Docker, the main UI service (`archon-ui`) is typically exposed on port `3737` as configured in the root `docker-compose.yml` and `.env` files. Please refer to the main project's `README.md` for more details on the Docker setup.

### 5. Running Tests
This project uses Vitest for unit testing. To run the tests:
```bash
npm test
```
