extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
    if event_bus != null:
        event_bus.request_play_card.connect(_on_request_play_card)
    
    manager.set_mask_transparent()
    await manager.show_dialog("很好！你抽出了晶片。\n現在，按住『綠色』的高相似度資料晶片，將它『拖曳 (Drag)』到中央的 Play Area！", false)
    var current_scene: Node = manager.get_tree().current_scene
    if current_scene:
        var hand_container: Node = current_scene.find_child("HandContainer", true, false)
        if hand_container:
            manager.focus_node(hand_container)

func exit() -> void:
    manager.unfocus()
    var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
    if event_bus != null:
        event_bus.request_play_card.disconnect(_on_request_play_card)

func _on_request_play_card(card_data: Resource) -> void:
    if card_data.get("type") == 2:
        # Successfully dragged a data card
        transitioned.emit("Deliver")
