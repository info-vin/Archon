export const markdownComponents = {
  p: ({ children }: any) => <p className="mb-4 leading-relaxed">{children}</p>,
  h1: ({ children }: any) => <h1 className="text-xl font-bold mb-3 mt-6">{children}</h1>,
  h2: ({ children }: any) => <h2 className="text-lg font-bold mb-3 mt-5">{children}</h2>,
  h3: ({ children }: any) => <h3 className="text-base font-semibold mb-2 mt-4">{children}</h3>,
  ul: ({ children }: any) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
  ol: ({ children }: any) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
  li: ({ children }: any) => <li className="leading-relaxed">{children}</li>,
  code: ({ children }: any) => <code className="px-1.5 py-0.5 rounded bg-black/30">{children}</code>,
};
