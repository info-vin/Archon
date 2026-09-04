import React, { useEffect } from 'react';
import { useMachine } from '@xstate/react';
import { approvalMachine } from '../machines/approvalMachine';
import { ProposedChange } from '@/types';

export interface UnifiedProposal extends ProposedChange {
  is_marketing?: boolean;
  marketing_type?: string;
  marketing_id?: string;
  marketing_title?: string;
  marketing_content?: string;
  marketing_author?: string;
}

export const useApprovalInbox = () => {
  const [state, send] = useMachine(approvalMachine);

  useEffect(() => {
    send({ type: 'FETCH' });
  }, [send]);

  // Phase 5.1.3: Deep linking support for AI proposals
  useEffect(() => {
    if (state.matches('idle') && state.context.proposals.length > 0) {
      const params = new URLSearchParams(window.location.search);
      const targetId = params.get('id');
      if (targetId && state.context.selectedId !== targetId) {
        send({ type: 'SELECT', id: targetId });
      }
    }
  }, [state.matches('idle'), state.context.proposals.length, state.context.selectedId, send]);

  const fetchData = () => send({ type: 'FETCH' });
  
  const setSelectedId = (id: string | null) => {
    if (id) send({ type: 'SELECT', id });
  };
  
  const setShowRejectInput = (show: boolean) => {
    if (show && state.context.selectedId) {
      send({ type: 'REJECT_INIT', id: state.context.selectedId });
    } else {
      send({ type: 'REJECT_CANCEL' });
    }
  };
  
  const setRejectReason = (reason: string) => {
    send({ type: 'SET_REJECT_REASON', reason });
  };

  // PERFORMANCE: Precalculate a Map for O(1) proposal lookups to eliminate O(N) Array.find() overhead on every render/interaction
  const proposalMap = React.useMemo(() => {
    const map = new Map<string, UnifiedProposal>();
    state.context.proposals.forEach(p => map.set(p.id, p));
    return map;
  }, [state.context.proposals]);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    const proposal = proposalMap.get(id);
    if (!proposal) return;

    if (action === 'approve') {
       send({ type: 'APPROVE', id });
    } else {
       if (proposal.is_marketing && !state.context.showRejectInput) {
           send({ type: 'REJECT_INIT', id });
       } else {
           send({ type: 'REJECT_SUBMIT', id });
       }
    }
  };

  const handleGenerateAIReason = async () => {
    send({ type: 'GENERATE_AI_REASON' });
  };

  return {
      proposals: state.context.proposals,
      loading: state.matches('loading'),
      error: state.matches('error') ? state.context.error : null,
      actionError: !state.matches('error') ? state.context.error : null,
      selectedId: state.context.selectedId,
      setSelectedId,
      selectedProposal: state.context.selectedId ? (proposalMap.get(state.context.selectedId) || null) : null,
      processingId: state.context.processingId,
      showRejectInput: state.context.showRejectInput,
      setShowRejectInput,
      rejectReason: state.context.rejectReason,
      setRejectReason,
      generatingReason: state.context.generatingReason || state.matches('generatingReason'),
      fetchData,
      handleAction,
      handleGenerateAIReason
  };
};
