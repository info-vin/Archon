with open("enduser-ui-fe/src/features/dashboard/components/ListView.tsx", "r") as f:
    content = f.read()

search_str = """            <li key={task.id} onClick={() => setEditingTask(task)} className="group relative overflow-hidden bg-white/70 backdrop-blur-md rounded-xl border border-white/50 shadow-sm hover:shadow-md transition-all cursor-pointer p-4 pl-5">"""
replace_str = """            <li
                key={task.id}
                onClick={() => setEditingTask(task)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setEditingTask(task);
                    }
                }}
                tabIndex={0}
                role="button"
                aria-label={`View details for task: ${task.title}`}
                className="group relative overflow-hidden bg-white/70 backdrop-blur-md rounded-xl border border-white/50 shadow-sm hover:shadow-md transition-all cursor-pointer p-4 pl-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
            >"""

if search_str in content:
    with open("enduser-ui-fe/src/features/dashboard/components/ListView.tsx", "w") as f:
        f.write(content.replace(search_str, replace_str))
    print("ListView.tsx updated successfully.")
else:
    print("Could not find the target string in ListView.tsx.")
