import React from 'react';
import { useMachine } from '@xstate/react';
import { imagePickerMachine } from '../machines/imagePickerMachine';
import { ImageIcon, SearchIcon, RefreshCwIcon, CheckCircleIcon, XIcon } from 'lucide-react';

interface SmartImagePickerProps {
  onSelect: (imageUrl: string) => void;
  onClose: () => void;
}

export const SmartImagePicker: React.FC<SmartImagePickerProps> = ({ onSelect, onClose }) => {
  const [state, send] = useMachine(imagePickerMachine);
  const { keyword, images, selectedImage, error } = state.context;
  const isSearching = state.matches('searching');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (keyword.trim()) {
      send({ type: 'SEARCH', keyword });
    }
  };

  const handleConfirm = () => {
    if (selectedImage) {
      send({ type: 'CONFIRM' });
      onSelect(selectedImage.url);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 data-testid="image-picker-modal-title" className="text-lg font-bold flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-indigo-600" />
            Smart Image Picker
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors" aria-label="Close Smart Image Picker">
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 bg-gray-50 border-b border-gray-100">
          <form onSubmit={handleSearch} className="relative flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                data-testid="image-search-input"
                value={keyword}
                onChange={(e) => send({ type: 'UPDATE_KEYWORD', keyword: e.target.value })}
                placeholder="Search high-quality images (e.g., 'business meeting')..."
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                id="search-input"
              />
              <SearchIcon className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
            </div>
            <button
              type="submit"
              data-testid="image-search-submit-btn"
              disabled={isSearching}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-bold disabled:opacity-50 flex items-center gap-2"
            >
              {isSearching ? <RefreshCwIcon className="w-4 h-4 animate-spin" /> : 'Search'}
            </button>
          </form>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-4 bg-white min-h-[300px]">
          {isSearching ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <RefreshCwIcon className="w-8 h-8 animate-spin mb-4" />
              <p>Searching smart assets...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full text-red-500">
              <p className="font-bold mb-2">Error searching images</p>
              <p className="text-sm mb-4">{error}</p>
              <button onClick={() => send({ type: 'RETRY' })} className="px-6 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-xl text-sm font-bold transition-colors">
                Retry
              </button>
            </div>
          ) : images.length === 0 && state.matches('success') ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <p>No images found. Try a different keyword.</p>
            </div>
          ) : images.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {images.map((img) => (
                <div
                  key={img.id}
                  onClick={() => send({ type: 'SELECT', image: img })}
                  className={`relative cursor-pointer rounded-xl overflow-hidden aspect-video border-4 transition-all ${
                    selectedImage?.id === img.id ? 'border-indigo-600 scale-95 shadow-lg' : 'border-transparent hover:scale-105'
                  }`}
                >
                  <img src={img.thumbnail} alt={img.author} className="w-full h-full object-cover bg-gray-100" />
                  {selectedImage?.id === img.id && (
                    <div className="absolute top-2 right-2 bg-indigo-600 text-white rounded-full p-1 shadow-sm">
                      <CheckCircleIcon className="w-4 h-4" />
                    </div>
                  )}
                  <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 pt-6">
                    <p className="text-white text-xs font-medium truncate">By {img.author}</p>
                    <p className="text-gray-300 text-[10px] uppercase tracking-wider">via {img.source}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <p>Enter a keyword to search for images.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
          <button onClick={onClose} className="px-6 py-2 rounded-xl font-bold text-gray-600 hover:bg-gray-200 transition-colors">
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selectedImage}
            className="px-6 py-2 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Insert Image
          </button>
        </div>
      </div>
    </div>
  );
};
