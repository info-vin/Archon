import React from 'react';
import { Eye, Settings, Download } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { DimensionBadge } from './DimensionBadge';
import { ModelInfo } from '../../types/ModelInterfaces';

export interface OllamaModelCardProps {
  model: ModelInfo;
  isSelected: boolean;
  onSelect: () => void;
}

export const OllamaModelCard: React.FC<OllamaModelCardProps> = ({ model, isSelected, onSelect }) => {
  const getCardBorderColor = () => {
    switch (model.archon_compatibility) {
      case 'full': return 'border-green-500/50';
      case 'partial': return 'border-orange-500/50';
      case 'limited': return 'border-red-500/50';
      default: return 'border-gray-500/50';
    }
  };

  const formatFileSize = (mb: number) => {
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${Math.round(mb)} MB`;
  };

  const formatContext = (tokens: number) => {
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
    if (tokens >= 1000) return `${Math.round(tokens / 1000)}K`;
    return tokens.toString();
  };

  const formatContextDetails = (model: ModelInfo) => {
    if (model.context_info) {
      const { current, max, min: base } = model.context_info;
      const parts = [];
      if (current) parts.push(`Current: ${formatContext(current)}`);
      if (max && max !== current) parts.push(`Max: ${formatContext(max)}`);
      if (base && base !== current && base !== max) parts.push(`Base: ${formatContext(base)}`);
      if (parts.length > 0) return parts.join(' | ');
    }
    return model.context_length ? `Context: ${formatContext(model.context_length)}` : 'Unknown';
  };

  return (
    <div 
      className={`relative bg-gray-800/50 rounded-xl p-4 border-2 transition-all duration-300 cursor-pointer hover:shadow-lg hover:scale-[1.02] ${
        isSelected ? `${getCardBorderColor()} ring-2 ring-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.3)]` : `${getCardBorderColor()} hover:border-gray-600 hover:bg-gray-800/70`
      }`}
      onClick={onSelect}
    >
      <div className="absolute top-3 right-3 flex gap-2">
        {model.model_type === 'embedding' && model.embedding_dimensions && (
          <DimensionBadge dimensions={model.embedding_dimensions} />
        )}
        {model.model_type === 'chat' && (
          <StatusBadge level={model.archon_compatibility} />
        )}
      </div>

      <div className="mb-3">
        <h3 className="text-white font-semibold text-lg mb-1">{model.name}</h3>
        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-sm capitalize">{model.model_type}</span>
          {model.capabilities && model.capabilities.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {model.capabilities.map((capability: string) => (
                <span key={capability} className="px-2 py-1 bg-blue-600/20 border border-blue-500/30 rounded-md text-xs text-blue-300 font-medium">
                  {capability}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {model.description && (
        <p className="text-gray-400 text-sm mb-3 line-clamp-2">{model.description}</p>
      )}

      <div className="border-t border-gray-600 pt-3">
        <div className="flex flex-wrap gap-4 text-xs">
          {model.model_type === 'chat' && (model.context_length || model.context_info) && (
            <div className="flex items-center">
              <Eye className="w-3 h-3 text-blue-400 mr-1" />
              <span className="text-gray-300">Context: </span>
              <span className="text-blue-400 ml-1">{formatContextDetails(model)}</span>
            </div>
          )}

          {model.size_mb && (
            <div className="flex items-center">
              <Download className="w-3 h-3 text-gray-400 mr-1" />
              <span className="text-gray-300">Size: </span>
              <span className="text-white ml-1">{formatFileSize(model.size_mb)}</span>
            </div>
          )}

          {model.parameters && (
            <div className="flex items-center">
              <Settings className="w-3 h-3 text-green-400 mr-1" />
              <span className="text-gray-300">Params: </span>
              <span className="text-green-400 ml-1">
                {typeof model.parameters === 'object' 
                  ? `${model.parameters.parameter_size || 'Unknown size'} ${model.parameters.quantization ? `(${model.parameters.quantization})` : ''}`.trim()
                  : model.parameters
                }
              </span>
            </div>
          )}

          {model.architecture && (
            <div className="flex items-center">
              <span className="w-3 h-3 text-purple-400 mr-1">🏗️</span>
              <span className="text-gray-300">Arch: </span>
              <span className="text-purple-400 ml-1 capitalize">{model.architecture}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
