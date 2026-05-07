import { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { ProposedChange, ChangeType } from '@/types';

export interface UnifiedProposal extends ProposedChange {
  is_marketing?: boolean;
  marketing_type?: string;
  marketing_id?: string;
  marketing_title?: string;
  marketing_content?: string;
  marketing_author?: string;
}

export const useApprovalInbox = () => {
  const [proposals, setProposals] = useState<UnifiedProposal[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // AI Reject flow states
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [generatingReason, setGeneratingReason] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setShowRejectInput(false);
    setRejectReason('');
    try {
      const [devChanges, marketingApprovals] = await Promise.all([
        api.getPendingChanges().catch(() => []),
        api.getPendingApprovals().catch(() => ({ blogs: [], leads: [] }))
      ]);
      
      const unifiedList: UnifiedProposal[] = [
        ...devChanges.map((c: any) => ({ ...c, is_marketing: false })),
        ...(marketingApprovals.blogs || []).map((b: any) => ({
          id: `mkt-blog-${b.id}`,
          created_at: b.created_at || b.publishDate || new Date().toISOString(),
          status: b.status,
          type: ChangeType.BLOG,
          change_summary: `Review Blog: ${b.title}`,
          request_payload: { new_content: b.content || b.excerpt },
          is_marketing: true,
          marketing_type: 'blog',
          marketing_id: b.id,
          marketing_title: b.title,
          marketing_content: b.content || b.excerpt,
          marketing_author: b.authorName
        }))
      ];
      
      unifiedList.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      setProposals(unifiedList);
      if (unifiedList.length > 0 && !selectedId) {
        setSelectedId(unifiedList[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch proposals');
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const selectedProposal = proposals.find(p => p.id === selectedId) || null;

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    const proposal = proposals.find(p => p.id === id);
    if (!proposal) return;

    if (action === 'reject' && !showRejectInput && proposal.is_marketing) {
       setShowRejectInput(true);
       return;
    }

    setProcessingId(id);
    try {
      if (proposal.is_marketing) {
         await api.processApproval(
             proposal.marketing_type || 'blog', 
             proposal.marketing_id!, 
             action, 
             action === 'reject' ? rejectReason : undefined
         );
      } else {
         if (action === 'approve') {
           await api.approveChange(id);
         } else {
           await api.rejectChange(id);
         }
      }
      
      setProposals(prev => prev.filter(p => p.id !== id));
      if (selectedId === id) {
        setSelectedId(null);
      }
      setShowRejectInput(false);
      setRejectReason('');
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleGenerateAIReason = async () => {
      if (!selectedProposal || !selectedProposal.marketing_id) return;
      setGeneratingReason(true);
      try {
         const res = await api.generateRejectReason(
             selectedProposal.marketing_type || 'blog', 
             selectedProposal.marketing_id
         );
         if (res && res.notes) {
             setRejectReason(res.notes);
         } else {
             setRejectReason('The content does not align with our current brand guidelines. Please revise the tone to be more professional.');
         }
      } catch (err: any) {
          setRejectReason('Failed to generate AI reason. Please enter manually.');
      } finally {
          setGeneratingReason(false);
      }
  };

  return {
      proposals,
      loading,
      error,
      selectedId,
      setSelectedId,
      selectedProposal,
      processingId,
      showRejectInput,
      setShowRejectInput,
      rejectReason,
      setRejectReason,
      generatingReason,
      fetchData,
      handleAction,
      handleGenerateAIReason
  };
};