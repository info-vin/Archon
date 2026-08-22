with open('enduser-ui-fe/src/features/team/components/AiCollaborationWidget.tsx', 'r') as f:
    content = f.read()

search = """            <div
                onClick={onClick}
                className={`bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row items-center gap-8 min-h-[200px] ${onClick ? 'cursor-pointer hover:border-indigo-200 hover:shadow-md transition-all group' : ''}`}
            >"""

replace = """            <div
                onClick={onClick}
                onKeyDown={(e) => {
                    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault();
                        onClick();
                    }
                }}
                role={onClick ? 'button' : undefined}
                tabIndex={onClick ? 0 : undefined}
                aria-label={onClick ? 'View token consumption details' : undefined}
                className={`bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row items-center gap-8 min-h-[200px] ${onClick ? 'cursor-pointer hover:border-indigo-200 hover:shadow-md transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2' : ''}`}
            >"""

content = content.replace(search, replace)

with open('enduser-ui-fe/src/features/team/components/AiCollaborationWidget.tsx', 'w') as f:
    f.write(content)
