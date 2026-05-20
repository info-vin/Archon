import { useState, useMemo } from "react";
import { FileText, Search } from "lucide-react";
import { Input } from "@/features/ui/primitives/input";
import { cn } from "@/features/ui/primitives/styles";
import { MOCK_DOCUMENTS } from "../../mock/projectsMock";

const searchableDocs = MOCK_DOCUMENTS.map((d) => d.title.toLowerCase());

export const ProjectDocView = ({ doc, onDocSelect }: { doc: any; onDocSelect: (doc: any) => void }) => {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredDocs = useMemo(() => {
    if (!searchQuery) return MOCK_DOCUMENTS;
    const query = searchQuery.toLowerCase();
    return MOCK_DOCUMENTS.filter((_, i) => searchableDocs[i].includes(query));
  }, [searchQuery]);

  return (
    <div className="flex h-[600px] gap-6 font-sans">
      <div className="w-64 flex flex-col space-y-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-700 dark:text-gray-300" />
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Documents</h3>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex-1 space-y-1">
          {filteredDocs.map((d) => (
            <button
              key={d.id}
              type="button"
              onClick={() => onDocSelect(d)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg transition-all",
                d.id === doc.id
                  ? "bg-cyan-500/10 text-cyan-700 border-l-2 border-cyan-500"
                  : "text-gray-600 hover:bg-white/5 border-l-2 border-transparent",
              )}
            >
              <div className="font-medium text-sm line-clamp-1">{d.title}</div>
              <div className="text-xs text-gray-500 mt-0.5">{d.type}</div>
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">{doc.title}</h2>
        <div className="text-gray-600 dark:text-gray-400 space-y-4">
          <p>
            Document type: <span className="px-2 py-1 text-xs bg-blue-500/10 text-blue-600 rounded">{doc.type}</span>
          </p>
          <p>This area shows the full document content with rich formatting and embedded media.</p>
        </div>
      </div>
    </div>
  );
};
