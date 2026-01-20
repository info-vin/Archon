import { test, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { BrandLogo } from '../../src/components/BrandLogo';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';

// Setup Mock for the SVG asset
// This simulates the state AFTER DevBot has done its job
const MOCK_SVG = '<svg data-testid="eciton-svg"><circle cx="50" cy="50" r="40" /></svg>';

test('BrandLogo renders fallback when asset is missing', async () => {
    // 1. Mock 404 for the logo
    server.use(
        http.get('/logo-eciton.svg', () => {
            return new HttpResponse(null, { status: 404 });
        })
    );

    render(<BrandLogo />);

    // 2. Expect "M" fallback text
    await waitFor(() => {
        expect(screen.getByText('M')).toBeInTheDocument();
        expect(screen.getByText('Myrmidon')).toBeInTheDocument();
    });
});

test('BrandLogo renders SVG when asset exists (DevBot Success)', async () => {
    // 1. Mock 200 for the logo
    server.use(
        http.get('/logo-eciton.svg', () => {
            return new HttpResponse(MOCK_SVG, {
                headers: { 'Content-Type': 'image/svg+xml' }
            });
        })
    );

    render(<BrandLogo />);

    // 2. Expect SVG to be injected
    await waitFor(() => {
        // Since we use dangerouslySetInnerHTML, we check for the SVG structure
        const container = screen.getByText('Myrmidon').parentElement;
        expect(container?.innerHTML).toContain('<svg');
        expect(container?.innerHTML).not.toContain('>M<'); // Fallback should be gone
    });
});
