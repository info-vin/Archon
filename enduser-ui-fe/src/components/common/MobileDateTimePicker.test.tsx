import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MobileDateTimePicker } from './MobileDateTimePicker';

describe('MobileDateTimePicker Accessibility', () => {
    it('should have accessible controls when opened', () => {
        const onChange = vi.fn();
        render(<MobileDateTimePicker value="" onChange={onChange} label="Test Date" />);

        // Open the picker
        const triggerButton = screen.getByText('Set Date & Time');
        fireEvent.click(triggerButton);

        // Check for dialog role
        const dialog = screen.getByRole('dialog');
        expect(dialog).toBeInTheDocument();
        expect(dialog).toHaveAttribute('aria-label', 'Set Due Date');
        expect(dialog).toHaveAttribute('aria-modal', 'true');

        // Check for close button accessibility
        const closeButton = screen.getByLabelText('Close date picker');
        expect(closeButton).toBeInTheDocument();

        // Check for column accessibility
        // Day column
        expect(screen.getByLabelText('Increase Day')).toBeInTheDocument();
        expect(screen.getByLabelText('Decrease Day')).toBeInTheDocument();

        // Hour column
        expect(screen.getByLabelText('Increase Hour')).toBeInTheDocument();
        expect(screen.getByLabelText('Decrease Hour')).toBeInTheDocument();

        // Minute column
        expect(screen.getByLabelText('Increase Minute')).toBeInTheDocument();
        expect(screen.getByLabelText('Decrease Minute')).toBeInTheDocument();
    });
});
