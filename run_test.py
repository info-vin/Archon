import json

def parse_godot_project():
    with open("recontextualization/project.godot", "r") as f:
        content = f.read()
    if "translations=" not in content:
        print("Translation files NOT registered in project.godot!")

parse_godot_project()
