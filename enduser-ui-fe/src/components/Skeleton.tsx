export const Skeleton = ({ className }: { className?: string }) => (
    <div className={`animate-pulse bg-gray-200 dark:bg-slate-700/50 rounded ${className || ''}`}></div>
);
