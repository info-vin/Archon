with open('python/src/server/api_routes/marketing_api.py', 'r') as f:
    lines = f.readlines()

new_lines = []
imports = []
code = []

# Move imports to top
in_imports = True
for line in lines:
    if line.startswith("import ") or line.startswith("from "):
        imports.append(line)
    elif line.strip() == "":
        continue
    else:
        code.append(line)

final_content = "".join(imports) + "\n\n" + "".join(code)

with open('python/src/server/api_routes/marketing_api.py', 'w') as f:
    f.write(final_content)
