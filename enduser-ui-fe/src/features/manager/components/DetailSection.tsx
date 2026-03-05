import { MinimizeIcon, MaximizeIcon } from '../../../components/Icons';

export const DetailSection: React.FC<{
    title: string, 
    subtitle: string, 
    children: React.ReactNode, 
    icon?: React.ReactNode,
    isMaximized?: boolean,
    onToggleMaximize?: () => void
}> = ({title, subtitle, children, icon, isMaximized, onToggleMaximize}) => (
    <div className={`
        bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden animate-in slide-in-from-bottom-4 duration-500
        ${isMaximized ? 'fixed inset-4 z-[60] shadow-2xl flex flex-col' : ''}
    `}>
        <div className="p-6 border-b border-gray-50 flex items-start justify-between bg-gray-50/30">
            <div>
                <h3 className={`font-black text-gray-800 tracking-tight flex items-center gap-2 ${isMaximized ? 'text-2xl' : 'text-lg'}`}>
                    {icon} {title}
                </h3>
                <p className={`text-gray-500 font-medium mt-1 uppercase tracking-wide ${isMaximized ? 'text-sm' : 'text-xs'}`}>{subtitle}</p>
            </div>
            {onToggleMaximize && (
                <button 
                    onClick={onToggleMaximize}
                    className="p-2 hover:bg-gray-200/50 rounded-full transition-colors text-gray-400 hover:text-indigo-600"
                >
                    {isMaximized ? <MinimizeIcon className="w-6 h-6" /> : <MaximizeIcon className="w-5 h-5" />}
                </button>
            )}
        </div>
        <div className={`p-6 ${isMaximized ? 'flex-1 overflow-y-auto' : ''}`}>
            {children}
        </div>
    </div>
);
