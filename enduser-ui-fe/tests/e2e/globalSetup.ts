// enduser-ui-fe/tests/e2e/globalSetup.ts
import { execSync } from 'child_process';
import * as dotenv from 'dotenv';
import * as path from 'path';

export default async function setup() {
  console.log('🚀 [E2E Global Setup] Starting...');

  // Load environment variables from .env.test for this Node.js process
  // This is crucial to get VITE_API_URL and ENABLE_TEST_ENDPOINTS
  const envPath = path.resolve(__dirname, '../../../.env.test'); // Path from enduser-ui-fe/tests/e2e/ to project root
  const result = dotenv.config({ path: envPath });

  if (result.error) {
    console.error('❌ [E2E Global Setup] Error loading .env.test file. Ensure it exists at project root.');
    throw result.error;
  }

  const backendApiUrl = `http://localhost:8181`; // Default or derived from VITE_API_URL
  
  console.log('🚀 [E2E Global Setup] Triggering database reset via API...');
  
  try {
    try {
    // We expect the backend server to be running (e.g., via `make dev`)
    // and for ENABLE_TEST_ENDPOINTS=true to be set in its environment.
    execSync(
      `curl -X POST ${backendApiUrl}/api/test/reset-database`,
      { stdio: 'inherit' } // 'inherit' will show curl's output/errors in the test console
    );
    console.log('✅ [E2E Global Setup] Database reset API call successful.');
  } catch (error) {
    console.warn('⚠️ [E2E Global Setup] Could not connect to backend to reset database. Continuing with potentially stale data.');
    // Do not re-throw the error, allowing the test suite to continue.
  }
  } catch (error) {
    console.error('❌ [E2E Global Setup] Failed to reset database via API.');
    console.error('   Please ensure the backend server is running with ENABLE_TEST_ENDPOINTS=true.');
    // Re-throw the error to fail the test suite if DB reset fails
    throw error;
  }

  console.log('🎉 [E2E Global Setup] Complete.');
}
