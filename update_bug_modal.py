import re

with open("archon-ui-main/src/components/bug-report/BugReportModal.tsx", "r") as f:
    content = f.read()

content = content.replace(
    'className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"\n              >',
    'className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"\n                aria-label="Close bug report modal"\n              >'
)

with open("archon-ui-main/src/components/bug-report/BugReportModal.tsx", "w") as f:
    f.write(content)
