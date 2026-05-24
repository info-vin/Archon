import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SourceContextPane } from './SourceContextPane';

const mockContextData = {
  logs: [],
  context_summary: 'This is a summary of the workflow context.',
  rag_refs: [
    {
      content: 'Local video demonstration reference text.',
      metadata: {
        source: '/assets/videos/auto_demos/marketing_demo.mp4'
      }
    },
    {
      content: 'Standard documentation reference text.',
      metadata: {
        source: 'https://docs.archon.ai/standard'
      }
    }
  ]
};

describe('SourceContextPane Component', () => {
  it('should render RAG references with inline video when source is a video file', () => {
    const { container } = render(
      <SourceContextPane
        isContextOpen={true}
        isLoadingContext={false}
        contextData={mockContextData}
        onToggleContext={() => {}}
      />
    );

    // Verify video tag exists
    const video = container.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute('src', '/assets/videos/auto_demos/marketing_demo.mp4');
    expect(video).toHaveAttribute('controls');

    // Verify external link anchor wrappers are rendered for both refs
    const anchors = container.querySelectorAll('a[href]');
    expect(anchors.length).toBe(2);
    expect(anchors[0]).toHaveAttribute('href', '/assets/videos/auto_demos/marketing_demo.mp4');
    expect(anchors[1]).toHaveAttribute('href', 'https://docs.archon.ai/standard');
  });

  it('should display loading skeleton when isLoadingContext is true', () => {
    render(
      <SourceContextPane
        isContextOpen={true}
        isLoadingContext={true}
        contextData={null}
        onToggleContext={() => {}}
      />
    );

    expect(screen.getByText(/MarketBot is gathering intelligence/i)).toBeInTheDocument();
  });
});
