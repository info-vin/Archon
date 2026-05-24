import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RAGCitation } from './RAGCitation';

const mockCitations = [
  {
    id: '1',
    title: 'Rose Blooming Concept',
    url: '/assets/videos/auto_demos/gemini_intro.mp4',
    snippet: 'This is a 4-second video showing a rose blooming.'
  },
  {
    id: '2',
    title: 'Technical Docs',
    url: 'https://docs.archon.ai/workflows',
    snippet: 'Static text citation document.'
  }
];

describe('RAGCitation Component', () => {
  it('should render the citation badge button with proper ARIA attributes', () => {
    render(<RAGCitation citationId="1" citations={mockCitations} />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(button).toHaveAttribute('aria-label', 'Source citation 1: Rose Blooming Concept');
  });

  it('should toggle popover and render video player when citation url points to a video', () => {
    const { container } = render(<RAGCitation citationId="1" citations={mockCitations} />);
    const button = screen.getByRole('button');
    
    // Click button to open popover
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    // Popover title should be visible
    expect(screen.getByTestId('citation-popover-title')).toHaveTextContent('Rose Blooming Concept');

    // Should render HTML5 video element with correct source
    const video = container.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute('src', '/assets/videos/auto_demos/gemini_intro.mp4');
    expect(video).toHaveAttribute('controls');
  });

  it('should render only text snippet and no video player when citation url points to standard web doc', () => {
    const { container } = render(<RAGCitation citationId="2" citations={mockCitations} />);
    const button = screen.getByRole('button');
    
    // Click button to open popover
    fireEvent.click(button);

    // Verify video is not rendered, text snippet is rendered
    const video = container.querySelector('video');
    expect(video).not.toBeInTheDocument();
    expect(screen.getByText(/"Static text citation document."/i)).toBeInTheDocument();
  });
});
