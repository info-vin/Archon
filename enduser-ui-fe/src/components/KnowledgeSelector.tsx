import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api.ts';
import { XIcon, ChevronDownIcon, CheckCircleIcon, PaperclipIcon } from './Icons.tsx';

interface KnowledgeItem {
  source_id: string;
  title: string;
  knowledge_type: string;
  url?: string;
}

interface KnowledgeSelectorProps {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
}

export const KnowledgeSelector: React.FC<KnowledgeSelectorProps> = ({
  selectedIds,
  onChange,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setIsLoading(true);
        const data = await api.getKnowledgeItems();
        setItems(data);
      } catch (error) {
        console.error("Failed to fetch knowledge items:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (isOpen && items.length === 0) {
      fetchItems();
    }
  }, [isOpen, items.length]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleItem = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter(i => i !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  const filteredItems = items.filter(item => 
    item.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.source_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedItems = items.filter(item => selectedIds.includes(item.source_id));

  return (
    <div className="space-y-2" ref={dropdownRef}>
      <label className="block text-sm font-medium text-foreground">
        Reference Knowledge (RAG Context)
      </label>
      
      {/* Selected Tags Display */}
      <div className="flex flex-wrap gap-2 mb-2">
        {selectedItems.map(item => (
          <div 
            key={item.source_id}
            className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 border border-primary/20 rounded-md text-xs text-primary-foreground"
          >
            <PaperclipIcon className="w-3 h-3" />
            <span className="max-w-[150px] truncate">{item.title || item.source_id}</span>
            <button
              type="button"
              onClick={() => toggleItem(item.source_id)}
              className="hover:text-destructive transition-colors"
              disabled={disabled}
            >
              <XIcon className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Dropdown Toggle */}
      <div className="relative">
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          className={`w-full flex items-center justify-between px-3 py-2 border border-border rounded-md bg-input text-sm text-left focus:outline-none focus:ring-2 focus:ring-ring ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          disabled={disabled}
        >
          <span className={selectedIds.length === 0 ? "text-muted-foreground" : "text-foreground"}>
            {selectedIds.length === 0 
              ? "Select internal knowledge..." 
              : `${selectedIds.length} items selected`}
          </span>
          <ChevronDownIcon className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-md shadow-lg max-h-60 overflow-hidden flex flex-col">
            <div className="p-2 border-b border-border">
              <input
                type="text"
                placeholder="Search knowledge..."
                className="w-full px-2 py-1 text-sm bg-input border border-border rounded focus:outline-none focus:ring-1 focus:ring-ring"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                autoFocus
              />
            </div>
            
            <div className="overflow-y-auto flex-1">
              {isLoading ? (
                <div className="p-4 text-center text-sm text-muted-foreground">Loading knowledge...</div>
              ) : filteredItems.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">No items found</div>
              ) : (
                filteredItems.map(item => {
                  const isSelected = selectedIds.includes(item.source_id);
                  return (
                    <button
                      key={item.source_id}
                      type="button"
                      onClick={() => toggleItem(item.source_id)}
                      className={`w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-accent transition-colors ${isSelected ? 'bg-accent/50' : ''}`}
                    >
                      <div className="flex flex-col overflow-hidden">
                        <span className="font-medium truncate">{item.title || item.source_id}</span>
                        <span className="text-xs text-muted-foreground truncate italic">{item.knowledge_type}</span>
                      </div>
                      {isSelected && <CheckCircleIcon className="w-4 h-4 text-primary" />}
                    </button>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
      <p className="text-[10px] text-muted-foreground italic">
        * Admin manages the knowledge base in the Admin Panel.
      </p>
    </div>
  );
};
