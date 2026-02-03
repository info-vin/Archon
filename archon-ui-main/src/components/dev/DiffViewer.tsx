import React, { useEffect, useState } from "react";
import Prism from "prismjs";
import "prismjs/themes/prism-tomorrow.css"; // Dark theme
import "prismjs/components/prism-python";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-json";
import { cn } from "../../lib/utils"; // Assume utility exists or verify

interface DiffViewerProps {
  original: string;
  modified: string;
  language?: string;
  className?: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  original,
  modified,
  language = "python",
  className,
}) => {
  const [originalHtml, setOriginalHtml] = useState("");
  const [modifiedHtml, setModifiedHtml] = useState("");

  useEffect(() => {
    const highlight = (code: string) => {
        const grammar = Prism.languages[language] || Prism.languages.plaintext;
        return Prism.highlight(code, grammar, language);
    };
    setOriginalHtml(highlight(original));
    setModifiedHtml(highlight(modified));
  }, [original, modified, language]);

  return (
    <div className={cn("grid grid-cols-2 gap-0 border rounded-md overflow-hidden font-mono text-sm", className)}>
      {/* Left: Original */}
      <div className="bg-[#1e1e1e] border-r border-gray-700 overflow-auto max-h-[500px]">
        <div className="bg-gray-800 text-gray-400 px-4 py-2 text-xs uppercase sticky top-0">Original</div>
        <pre className="m-0 p-4">
            <code dangerouslySetInnerHTML={{ __html: originalHtml }} />
        </pre>
      </div>

      {/* Right: Modified */}
      <div className="bg-[#1e1e1e] overflow-auto max-h-[500px]">
        <div className="bg-green-900/30 text-green-400 px-4 py-2 text-xs uppercase sticky top-0">Modified</div>
        <pre className="m-0 p-4">
            <code dangerouslySetInnerHTML={{ __html: modifiedHtml }} />
        </pre>
      </div>
    </div>
  );
};
