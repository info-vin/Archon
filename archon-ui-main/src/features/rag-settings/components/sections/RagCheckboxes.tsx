import { Check } from "lucide-react";
import type React from "react";

interface RagCheckboxFieldProps {
  id: string;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label: string;
  description: string;
}

export const RagCheckboxField = ({ id, checked, onChange, label, description }: RagCheckboxFieldProps) => (
  <div className="flex items-start group">
    <div className="relative flex items-center h-5 mt-1">
      <input type="checkbox" id={id} checked={checked} onChange={onChange} className="sr-only peer" />
      <label
        htmlFor={id}
        className="w-5 h-5 rounded-md border border-gray-300 dark:border-gray-700 peer-checked:bg-green-500/20 peer-checked:border-green-500 cursor-pointer flex items-center justify-center"
      >
        <Check className={`w-3.5 h-3.5 text-green-500 transition-all ${checked ? "opacity-100" : "opacity-0"}`} />
      </label>
    </div>
    <div className="ml-3">
      <label htmlFor={id} className="text-sm font-medium text-gray-700 dark:text-zinc-300 cursor-pointer">
        {label}
      </label>
      <p className="text-[10px] text-gray-500 leading-tight">{description}</p>
    </div>
  </div>
);
