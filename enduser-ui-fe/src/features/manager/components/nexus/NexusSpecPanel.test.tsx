import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NexusSpecPanel } from './NexusSpecPanel';

vi.mock('@/components/Icons.tsx', () => ({
  XIcon: (props: any) => <svg data-testid="x-icon" {...props} />,
  SettingsIcon: (props: any) => <svg data-testid="settings-icon" {...props} />,
  FileTextIcon: (props: any) => <svg data-testid="file-text-icon" {...props} />
}));

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown-content">{children}</div>
}));

describe('NexusSpecPanel Component Hardening', () => {
  it('renders correctly', () => {
    render(<NexusSpecPanel isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText(/Nexus Metrics Spec/i)).toBeInTheDocument();
  });
});
