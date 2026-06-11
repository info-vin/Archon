with open("project.godot", "r") as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.startswith("window/size/viewport_width="):
        out.append("window/size/viewport_width=1152\n")
    elif line.startswith("window/size/viewport_height="):
        out.append("window/size/viewport_height=648\n")
    elif line.startswith("window/stretch/mode="):
        out.append("window/stretch/mode=\"canvas_items\"\n")
        out.append("window/stretch/aspect=\"keep\"\n")
    else:
        out.append(line)

with open("project.godot", "w") as f:
    f.writelines(out)
