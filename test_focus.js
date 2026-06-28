const fs = require('fs');
let code = fs.readFileSync('enduser-ui-fe/src/components/Button.tsx', 'utf8');

code = code.replace(/primary: `([^`]+)`/, 'primary: `$1      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-${c}-500 focus-visible:ring-offset-2\n    `');
code = code.replace(/secondary: `([^`]+)`/, 'secondary: `$1      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2\n    `');
code = code.replace(/outline: `([^`]+)`/, 'outline: `$1      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-${c}-500 focus-visible:ring-offset-2\n    `');
code = code.replace(/ghost: `([^`]+)`/, 'ghost: `$1      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2\n    `');
code = code.replace(/danger: `([^`]+)`/, 'danger: `$1      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2\n    `');

console.log(code);
