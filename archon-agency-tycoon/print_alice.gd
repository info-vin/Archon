extends SceneTree

func _init():
    var a = preload("res://Scripts/Resources/AgentResource.gd").new()
    print("New agent state: ", a.state)
    quit()
