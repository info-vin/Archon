import React, { createContext, useContext, useMemo, useState } from "react";
import type { KnowledgeItem } from "../types";

interface KnowledgeOptimisticContextType {
  optimisticCreates: KnowledgeItem[];
  optimisticUpdates: Record<string, Partial<KnowledgeItem>>;
  optimisticDeletes: Set<string>;
  addOptimisticCreate: (item: KnowledgeItem) => void;
  removeOptimisticCreate: (sourceId: string) => void;
  addOptimisticUpdate: (sourceId: string, updates: Partial<KnowledgeItem>) => void;
  removeOptimisticUpdate: (sourceId: string) => void;
  addOptimisticDelete: (sourceId: string) => void;
  removeOptimisticDelete: (sourceId: string) => void;
}

const KnowledgeOptimisticContext = createContext<KnowledgeOptimisticContextType | undefined>(undefined);

export const KnowledgeOptimisticProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [optimisticCreates, setOptimisticCreates] = useState<KnowledgeItem[]>([]);
  const [optimisticUpdates, setOptimisticUpdates] = useState<Record<string, Partial<KnowledgeItem>>>({});
  const [optimisticDeletes, setOptimisticDeletes] = useState<Set<string>>(new Set());

  const addOptimisticCreate = (item: KnowledgeItem) => {
    setOptimisticCreates((prev) => [item, ...prev]);
  };

  const removeOptimisticCreate = (sourceId: string) => {
    setOptimisticCreates((prev) => prev.filter((item) => item.source_id !== sourceId));
  };

  const addOptimisticUpdate = (sourceId: string, updates: Partial<KnowledgeItem>) => {
    setOptimisticUpdates((prev) => ({
      ...prev,
      [sourceId]: { ...(prev[sourceId] || {}), ...updates },
    }));
  };

  const removeOptimisticUpdate = (sourceId: string) => {
    setOptimisticUpdates((prev) => {
      const next = { ...prev };
      delete next[sourceId];
      return next;
    });
  };

  const addOptimisticDelete = (sourceId: string) => {
    setOptimisticDeletes((prev) => {
      const next = new Set(prev);
      next.add(sourceId);
      return next;
    });
  };

  const removeOptimisticDelete = (sourceId: string) => {
    setOptimisticDeletes((prev) => {
      const next = new Set(prev);
      next.delete(sourceId);
      return next;
    });
  };

  const value = useMemo(
    () => ({
      optimisticCreates,
      optimisticUpdates,
      optimisticDeletes,
      addOptimisticCreate,
      removeOptimisticCreate,
      addOptimisticUpdate,
      removeOptimisticUpdate,
      addOptimisticDelete,
      removeOptimisticDelete,
    }),
    [optimisticCreates, optimisticUpdates, optimisticDeletes]
  );

  return <KnowledgeOptimisticContext.Provider value={value}>{children}</KnowledgeOptimisticContext.Provider>;
};

export function useKnowledgeOptimistic() {
  const context = useContext(KnowledgeOptimisticContext);
  if (!context) {
    throw new Error("useKnowledgeOptimistic must be used within a KnowledgeOptimisticProvider");
  }
  return context;
}
