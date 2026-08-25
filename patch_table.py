with open("enduser-ui-fe/src/features/dashboard/components/TableView.tsx", "r") as f:
    content = f.read()

search_str = """            {tasks.map(task => (
              <tr key={task.id} onClick={() => setEditingTask(task)} className="hover:bg-white dark:hover:bg-slate-800/50 transition-colors cursor-pointer group">"""
replace_str = """            {tasks.map(task => (
              <tr
                key={task.id}
                onClick={() => setEditingTask(task)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setEditingTask(task);
                  }
                }}
                tabIndex={0}
                className="hover:bg-white dark:hover:bg-slate-800/50 transition-colors cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500"
              >"""

if search_str in content:
    with open("enduser-ui-fe/src/features/dashboard/components/TableView.tsx", "w") as f:
        f.write(content.replace(search_str, replace_str))
    print("TableView.tsx updated successfully.")
else:
    print("Could not find the target string in TableView.tsx.")
