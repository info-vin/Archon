import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import UserAvatar from './UserAvatar';

describe('UserAvatar', () => {
  it('should render the component', () => {
    render(<UserAvatar name="John Doe" />);
    const avatar = screen.getByTitle('John Doe');
    expect(avatar).toBeInTheDocument();
  });

  it('should display the correct initial from a full name', () => {
    render(<UserAvatar name="John Doe" />);
    const avatar = screen.getByText('J');
    expect(avatar).toBeInTheDocument();
  });

  it('should display the correct initial from a single name', () => {
    render(<UserAvatar name="Archon" />);
    const avatar = screen.getByText('A');
    expect(avatar).toBeInTheDocument();
  });

  it('should display a question mark if the name is empty', () => {
    render(<UserAvatar name="" />);
    const avatar = screen.getByText('?');
    expect(avatar).toBeInTheDocument();
  });

  it('should have the full name as the title attribute', () => {
    render(<UserAvatar name="Jane Smith" />);
    const avatar = screen.getByTitle('Jane Smith');
    expect(avatar).toBeInTheDocument();
  });

  it('should apply custom size when provided', () => {
    render(<UserAvatar name="Test" size={60} />);
    const avatar = screen.getByText('T');
    expect(avatar.style.width).toBe('60px');
    expect(avatar.style.height).toBe('60px');
  });
});
