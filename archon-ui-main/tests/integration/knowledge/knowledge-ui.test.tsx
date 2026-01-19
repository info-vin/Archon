import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { KnowledgeTable } from '../../../src/features/knowledge/components/KnowledgeTable';
import type { KnowledgeItem } from '../../../src/features/knowledge/types';
import { ToastProvider } from '../../../src/features/ui/components/ToastProvider';
import React from 'react';

// Mock the KnowledgePreviewModal - we only test its presence
vi.mock('../../../src/features/knowledge/components/KnowledgePreviewModal', () => ({
  KnowledgePreviewModal: ({ isOpen, title, onClose }: any) => isOpen ? (
    <div role="dialog" aria-label="Preview Modal">
      <h1>Preview: {title}</h1>
      <button onClick={onClose}>Close</button>
    </div>
  ) : null
}));

// Mock the hooks to avoid network and context issues
vi.mock('../../../src/features/knowledge/hooks', () => ({
  useDeleteKnowledgeItem: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ success: true })
  })
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const mockItems: KnowledgeItem[] = [
  {
    id: '1',
    source_id: 'src-1',
    title: '測試文件.pdf',
    url: 'http://localhost:54321/storage/v1/object/public/archon_documents/uploads/%E6%B8%AC%E8%A9%A6%E6%96%87%E4%BB%B6.pdf',
    source_type: 'file',
    knowledge_type: 'technical',
    status: 'completed',
    document_count: 10,
    code_examples_count: 5,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    metadata: {
      file_name: '測試文件.pdf',
      file_type: 'application/pdf',
    }
  }
];

describe('KnowledgeTable Integration (Admin UI)', () => {
  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          {ui}
        </ToastProvider>
      </QueryClientProvider>
    );
  };

  it('should render unicode title correctly', () => {
    renderWithProviders(
      <KnowledgeTable 
        items={mockItems} 
        onViewDocument={vi.fn()} 
        onDeleteSuccess={vi.fn()} 
      />
    );

    // Verify Chinese title is rendered correctly
    expect(screen.getByText('測試文件.pdf')).toBeInTheDocument();
  });

  it('should open preview modal when preview button is clicked', async () => {
    renderWithProviders(
      <KnowledgeTable 
        items={mockItems} 
        onViewDocument={vi.fn()} 
        onDeleteSuccess={vi.fn()} 
      />
    );

    // Find the Preview button (icon mocked as text 'FileSearch')
    const previewBtn = screen.getByTitle('Preview');
    expect(previewBtn).toBeInTheDocument();

    // Click it
    fireEvent.click(previewBtn);

    // Verify Modal opens
    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: 'Preview Modal' })).toBeInTheDocument();
      expect(screen.getByText('Preview: 測試文件.pdf')).toBeInTheDocument();
    });
  });
});
