with open("enduser-ui-fe/src/features/dashboard/components/KanbanView.tsx", "r") as f:
    content = f.read()

search_str = """                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => onDragStart(e, task.id)}
                    onClick={() => setEditingTask(task)}
                    className="relative bg-white p-4 rounded-xl shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing overflow-hidden transition-all group border border-gray-100"
                  >"""
replace_str = """                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => onDragStart(e, task.id)}
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
                    className="relative bg-white p-4 rounded-xl shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing overflow-hidden transition-all group border border-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
                  >"""

if search_str in content:
    with open("enduser-ui-fe/src/features/dashboard/components/KanbanView.tsx", "w") as f:
        f.write(content.replace(search_str, replace_str))
    print("KanbanView.tsx updated successfully.")
else:
    print("Could not find the target string in KanbanView.tsx.")
