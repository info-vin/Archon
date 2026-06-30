extends SceneTree

func _init():
    var registry = load("res://src/managers/CardRegistry.gd").new()
    registry._ready()
    print("Cards loaded: ", registry.cards.keys())
    quit()
