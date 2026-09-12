export const markdownComponents = {
  h1: ({ ...props }: any) => <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 mt-6" {...props} />,
  h2: ({ ...props }: any) => <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3 mt-5" {...props} />,
  h3: ({ ...props }: any) => <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 mt-4" {...props} />,
  p: ({ ...props }: any) => <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 leading-relaxed" {...props} />,
  ul: ({ ...props }: any) => <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 mb-3 space-y-1" {...props} />,
  ol: ({ ...props }: any) => <ol className="list-decimal list-inside text-sm text-gray-700 dark:text-gray-300 mb-3 space-y-1" {...props} />,
  li: ({ ...props }: any) => <li className="ml-4" {...props} />,
  code: ({ ...props }: any) => <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs font-mono text-cyan-600 dark:text-cyan-400" {...props} />,
  pre: ({ ...props }: any) => <pre className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg overflow-x-auto mb-3" {...props} />,
  a: ({ ...props }: any) => <a className="text-cyan-600 dark:text-cyan-400 hover:underline" {...props} />,
  blockquote: ({ ...props }: any) => <blockquote className="border-l-4 border-gray-300 dark:border-gray-700 pl-4 italic text-gray-600 dark:text-gray-400 my-3" {...props} />,
};
