import sys

with open("archon-ui-main/src/features/projects/views/ProjectsView.tsx", "r") as f:
    content = f.read()

# Replace find() with get from map
search_block = """
  // Auto-select project based on URL
  useEffect(() => {
    if (!sortedProjects.length) return;

    // If there's a projectId in the URL, select that project
    if (projectId) {
      const project = sortedProjects.find((p) => p.id === projectId);
      if (project) {
"""

replace_block = """
  // Auto-select project based on URL
  useEffect(() => {
    if (!sortedProjects.length) return;

    // If there's a projectId in the URL, select that project
    if (projectId) {
      const projectMap = new Map((projects as Project[]).map(p => [p.id, p]));
      const project = projectMap.get(projectId);
      if (project) {
"""

content = content.replace(search_block, replace_block)

search_block2 = """
  // Handle pin toggle
  const handlePinProject = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    const project = (projects as Project[]).find((p) => p.id === projectId);
    if (!project) return;
"""

replace_block2 = """
  // Handle pin toggle
  const handlePinProject = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    const projectMap = new Map((projects as Project[]).map(p => [p.id, p]));
    const project = projectMap.get(projectId);
    if (!project) return;
"""

content = content.replace(search_block2, replace_block2)


with open("archon-ui-main/src/features/projects/views/ProjectsView.tsx", "w") as f:
    f.write(content)
