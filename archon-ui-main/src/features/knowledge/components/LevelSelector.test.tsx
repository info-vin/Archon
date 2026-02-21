import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LevelSelector } from './LevelSelector';

// Mock dependencies to avoid complex rendering issues
vi.mock('../../ui/primitives/tooltip', () => ({
  SimpleTooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Tooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock lucide-react to include Info icon which is missing in global setup
vi.mock('lucide-react', () => ({
  Info: () => <div data-testid="info-icon">Info</div>,
  Check: () => <div data-testid="check-icon">Check</div>, // In case it's used
  Minus: () => <div data-testid="minus-icon">Minus</div>, // In case it's used
}));

describe('LevelSelector', () => {
  it('renders all options and allows tabbing to all options', () => {
    // Render with Level 1 selected
    render(<LevelSelector value="1" onValueChange={() => {}} />);

    // Level 1 is selected
    const btn1 = screen.getByRole('radio', { name: /Level 1/i });
    expect(btn1).toBeInTheDocument();
    expect(btn1).toHaveAttribute('aria-checked', 'true');
    // Selected item should be focusable
    expect(btn1).not.toHaveAttribute('tabIndex', '-1');

    // Check actual focusability
    btn1.focus();
    expect(document.activeElement).toBe(btn1);

    // Level 2 is NOT selected.
    // In current implementation, unselected items have tabIndex="-1", making them unreachable via Tab key.
    // We want them to be reachable (tabIndex="0" or no tabIndex attribute).
    const btn2 = screen.getByRole('radio', { name: /Level 2/i });
    expect(btn2).toBeInTheDocument();
    expect(btn2).toHaveAttribute('aria-checked', 'false');

    // This assertion expects the FIX to be applied (no tabIndex="-1")
    expect(btn2).not.toHaveAttribute('tabIndex', '-1');

    // Check actual focusability for unselected item
    btn2.focus();
    expect(document.activeElement).toBe(btn2);
  });
});
