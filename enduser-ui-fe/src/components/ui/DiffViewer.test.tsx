// src/components/DiffViewer.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import DiffViewer from './DiffViewer';
import '@testing-library/jest-dom';

// Mock the react-diff-viewer library since we are only testing our wrapper component
vi.mock('react-diff-viewer', () => ({
  default: ({ oldValue, newValue }: { oldValue: string, newValue: string }) => (
    <div>
      <div data-testid="old-content">{oldValue}</div>
      <div data-testid="new-content">{newValue}</div>
    </div>
  ),
}));

describe('DiffViewer', () => {
  it('renders old and new content correctly', () => {
    const oldContent = 'Hello world';
    const newContent = 'Hello, beautiful world!';

    render(<DiffViewer oldContent={oldContent} newContent={newContent} />);

    // Check if both old and new content are displayed by the mocked component
    expect(screen.getByTestId('old-content')).toHaveTextContent(oldContent);
    expect(screen.getByTestId('new-content')).toHaveTextContent(newContent);
  });

  it('handles empty content without crashing', () => {
    render(<DiffViewer oldContent="" newContent="" />);
    expect(screen.getByTestId('old-content')).toBeEmptyDOMElement();
    expect(screen.getByTestId('new-content')).toBeEmptyDOMElement();
  });
});
