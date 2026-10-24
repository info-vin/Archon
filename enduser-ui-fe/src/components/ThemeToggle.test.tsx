import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import ThemeToggle from './ThemeToggle';

describe('ThemeToggle Accessibility & UX', () => {
    beforeEach(() => {
        localStorage.clear();
        document.documentElement.classList.remove('dark');
    });

    it('renders with type="button" and accessible attributes in light mode default', () => {
        render(<ThemeToggle />);
        const button = screen.getByRole('button', { name: /switch to dark theme/i });

        expect(button).toBeInTheDocument();
        expect(button).toHaveAttribute('type', 'button');
        expect(button).toHaveAttribute('aria-pressed', 'false');

        const svg = button.querySelector('svg');
        expect(svg).toBeInTheDocument();
        expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('toggles theme state and updates aria attributes when clicked', () => {
        render(<ThemeToggle />);
        const button = screen.getByRole('button', { name: /switch to dark theme/i });

        fireEvent.click(button);

        expect(button).toHaveAttribute('aria-label', 'Switch to light theme');
        expect(button).toHaveAttribute('aria-pressed', 'true');
        expect(document.documentElement.classList.contains('dark')).toBe(true);
        expect(localStorage.getItem('theme')).toBe('dark');

        fireEvent.click(button);

        expect(button).toHaveAttribute('aria-label', 'Switch to dark theme');
        expect(button).toHaveAttribute('aria-pressed', 'false');
        expect(document.documentElement.classList.contains('dark')).toBe(false);
        expect(localStorage.getItem('theme')).toBe('light');
    });
});
