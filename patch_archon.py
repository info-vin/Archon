with open("archon-ui-main/src/features/knowledge/inspector/components/ContentViewer.tsx", "r") as f:
    content = f.read()

old_components = """              components={{
                p: ({ children }) => <p className="mb-4 leading-relaxed">{children}</p>,
                h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-6">{children}</h1>,
                h2: ({ children }) => <h2 className="text-lg font-bold mb-3 mt-5">{children}</h2>,
                h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-4">{children}</h3>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                code: ({ children }) => <code className="px-1.5 py-0.5 rounded bg-black/30">{children}</code>,
              }}"""

extracted_components = """const MARKDOWN_COMPONENTS = {
  p: ({ children }: any) => <p className="mb-4 leading-relaxed">{children}</p>,
  h1: ({ children }: any) => <h1 className="text-xl font-bold mb-3 mt-6">{children}</h1>,
  h2: ({ children }: any) => <h2 className="text-lg font-bold mb-3 mt-5">{children}</h2>,
  h3: ({ children }: any) => <h3 className="text-base font-semibold mb-2 mt-4">{children}</h3>,
  ul: ({ children }: any) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
  ol: ({ children }: any) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
  li: ({ children }: any) => <li className="leading-relaxed">{children}</li>,
  code: ({ children }: any) => <code className="px-1.5 py-0.5 rounded bg-black/30">{children}</code>,
};"""

if "const MARKDOWN_COMPONENTS =" not in content:
    content = content.replace("export const ContentViewer: React.FC<ContentViewerProps> = ({ selectedItem, onCopy, copiedId, sourceDocumentUrl }) => {", f"{extracted_components}\n\nexport const ContentViewer: React.FC<ContentViewerProps> = ({{ selectedItem, onCopy, copiedId, sourceDocumentUrl }}) => {{")

content = content.replace(old_components, "              components={MARKDOWN_COMPONENTS as any}")

with open("archon-ui-main/src/features/knowledge/inspector/components/ContentViewer.tsx", "w") as f:
    f.write(content)

# DocumentViewer
with open("archon-ui-main/src/features/projects/documents/components/DocumentViewer.tsx", "r") as f:
    content2 = f.read()

old_components2 = """            components={{
              h1: ({ ...props }) => (
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 mt-6" {...props} />
              ),
              h2: ({ ...props }) => (
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3 mt-5" {...props} />
              ),
              h3: ({ ...props }) => (
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 mt-4" {...props} />
              ),
              p: ({ ...props }) => (
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 leading-relaxed" {...props} />
              ),
              ul: ({ ...props }) => (
                <ul
                  className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 mb-3 space-y-1"
                  {...props}
                />
              ),
              ol: ({ ...props }) => (
                <ol
                  className="list-decimal list-inside text-sm text-gray-700 dark:text-gray-300 mb-3 space-y-1"
                  {...props}
                />
              ),
              li: ({ ...props }) => <li className="ml-4" {...props} />,
              code: ({ ...props }) => (
                <code
                  className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs font-mono text-cyan-600 dark:text-cyan-400"
                  {...props}
                />
              ),
              pre: ({ ...props }) => (
                <pre className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg overflow-x-auto mb-3" {...props} />
              ),
              a: ({ ...props }) => <a className="text-cyan-600 dark:text-cyan-400 hover:underline" {...props} />,
              blockquote: ({ ...props }) => (
                <blockquote
                  className="border-l-4 border-gray-300 dark:border-gray-700 pl-4 italic text-gray-600 dark:text-gray-400 my-3"
                  {...props}
                />
              ),
            }}"""

extracted_components2 = """const MARKDOWN_COMPONENTS = {
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
};"""

if "const MARKDOWN_COMPONENTS =" not in content2:
    content2 = content2.replace("export const DocumentViewer = ({ document, onSave }: DocumentViewerProps) => {", f"{extracted_components2}\n\nexport const DocumentViewer = ({{ document, onSave }}: DocumentViewerProps) => {{")

content2 = content2.replace(old_components2, "            components={MARKDOWN_COMPONENTS as any}")

with open("archon-ui-main/src/features/projects/documents/components/DocumentViewer.tsx", "w") as f:
    f.write(content2)
