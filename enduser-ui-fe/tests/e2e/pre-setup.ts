// enduser-ui-fe/tests/e2e/pre-setup.ts

// This file runs BEFORE any other setup files or tests.
// It is used to initialize the environment (like localStorage)
// so that modules imported by `vi.mock` (which are hoisted)
// can access these values immediately.

const mockUser = {
    id: 'user-e2e-1',
    employeeId: 'E2E001',
    name: 'E2E Test User',
    email: 'e2e@archon.com',
    department: 'QA',
    position: 'Tester',
    status: 'active',
    role: 'Admin',
    avatar: 'https://i.pravatar.cc/150?u=e2e@archon.com'
};

// Inject Supabase credentials into localStorage.
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://mock.supabase.co';
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY || 'mock-key';

if (supabaseUrl && supabaseAnonKey) {
  localStorage.setItem('supabaseUrl', supabaseUrl);
  localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
}

// Inject the mock user.
localStorage.setItem('user', JSON.stringify(mockUser));

console.log('✅ [Pre-Setup] Environment variables injected into localStorage.');
