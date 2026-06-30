extends SceneTree

func _init():
	print("Running full project with SceneTree hook")
	var root = get_root()
	var main_scene = load(ProjectSettings.get_setting("run/main_scene")).instantiate()
	root.add_child(main_menu)
