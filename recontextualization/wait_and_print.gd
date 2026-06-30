extends SceneTree

func _init():
	call_deferred("run_test")

func run_test():
	var root = get_root()
	# Check if EventBus node is under root too
	print("Has EventBus node under root: ", root.has_node("EventBus"))
	print("Has GameState node under root: ", root.has_node("GameState"))
	print("Has CardRegistry node under root: ", root.has_node("CardRegistry"))
	
	# Can we get them using get_node?
	var sm = root.get_node_or_null("SaveManager")
	print("SaveManager instance: ", sm)
	
	quit()
