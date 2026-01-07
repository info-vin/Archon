import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EmployeeRole } from '../types.ts';

// 1. Define Mocks BEFORE import
const mockGetSession = vi.fn();
const mockFrom = vi.fn();

vi.mock('@supabase/supabase-js', () => ({
    createClient: vi.fn(() => ({
        auth: {
            getSession: mockGetSession,
        },
        from: mockFrom
    }))
}));

// 2. Import the module under test
import { api, supabase } from './api.ts';

describe('API Stability & Auth Headers (Phase 6 Verification)', () => {
    
    beforeEach(() => {
        vi.clearAllMocks();
        global.fetch = vi.fn();
        
        // Default Mock Behavior
        mockFrom.mockReturnValue({
            select: vi.fn(() => ({
                eq: vi.fn(() => ({
                    single: vi.fn().mockResolvedValue({ data: null, error: null })
                }))
            })),
            insert: vi.fn().mockReturnValue({ select: vi.fn(() => ({ single: vi.fn() })) }),
            update: vi.fn().mockReturnValue({ select: vi.fn(() => ({ single: vi.fn() })) })
        });
    });

    it('should inject Authorization header into API requests when session exists', async () => {
        // Setup Session
        const mockToken = 'fake-jwt-token';
        mockGetSession.mockResolvedValue({
            data: { session: { access_token: mockToken, user: { id: 'user-123' } } },
            error: null
        });

        // Setup Fetch
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: async () => ({ tasks: [] })
        });

        // Act
        await api.getTasks();

        // Assert
        const fetchCalls = (global.fetch as any).mock.calls;
        expect(fetchCalls[0][1].headers).toHaveProperty('Authorization', `Bearer ${mockToken}`);
    });

    it('should fallback to session metadata if profiles table fetch fails (Fix for 406 Logout Loop)', async () => {
        // Setup Session
        mockGetSession.mockResolvedValue({
            data: { 
                session: { 
                    user: { 
                        id: 'user-123', 
                        email: 'test@example.com', 
                        user_metadata: { name: 'Fallback Name' } 
                    } 
                } 
            },
            error: null
        });

        // Setup Profile Fetch Failure (406)
        mockFrom.mockReturnValue({
            select: vi.fn(() => ({
                eq: vi.fn(() => ({
                    single: vi.fn().mockResolvedValue({
                        data: null,
                        error: { message: 'Not Acceptable', status: 406 }
                    })
                }))
            }))
        });

        // Act
        const user = await api.getCurrentUser();

        // Assert
        expect(user).not.toBeNull();
        expect(user?.name).toBe('Fallback Name');
    });
});