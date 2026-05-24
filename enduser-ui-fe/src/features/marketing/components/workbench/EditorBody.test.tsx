import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EditorBody } from './EditorBody';

const mockProps = {
  activeSource: {
    id: '1',
    title: 'Collaborative AI Workflow',
    type: 'blog' as const,
    score: 100,
    summary: 'Test summary',
    date: '2026-05-24'
  },
  isGeneratingImage: false,
  title: 'My Article Title',
  content: 'My content text',
  onGenerateImage: vi.fn(),
  onTitleChange: vi.fn(),
  onContentChange: vi.fn()
};

describe('EditorBody Component', () => {
  it('should render a video element when previewUrl points to a video', () => {
    const videoUrl = '/assets/videos/auto_demos/marketing_demo.mp4';
    const { container } = render(
      <EditorBody
        {...mockProps}
        previewUrl={videoUrl}
      />
    );

    // Verify video tag exists
    const video = container.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute('src', videoUrl);
    expect(video).toHaveAttribute('controls');
    expect(video).toHaveAttribute('loop');
    expect(video?.muted).toBe(true);

    // Verify img tag does not exist
    expect(container.querySelector('img')).not.toBeInTheDocument();
  });

  it('should render an image element when previewUrl points to an image', () => {
    const imageUrl = 'https://picsum.photos/seed/test/600/400';
    const { container } = render(
      <EditorBody
        {...mockProps}
        previewUrl={imageUrl}
      />
    );

    // Verify img tag exists
    const img = container.querySelector('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', imageUrl);

    // Verify video tag does not exist
    expect(container.querySelector('video')).not.toBeInTheDocument();
  });

  it('should trigger title change handlers correctly', () => {
    render(
      <EditorBody
        {...mockProps}
        previewUrl={null}
      />
    );

    const input = screen.getByLabelText('Article title');
    fireEvent.change(input, { target: { value: 'New Title' } });
    expect(mockProps.onTitleChange).toHaveBeenCalledWith('New Title');
  });
});
