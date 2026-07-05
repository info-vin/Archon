extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    # Connect to the event bus to listen for cards being drawn (which happens after search)
    var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
    if event_bus != null:
        event_bus.card_drawn.connect(_on_card_drawn)
    
    manager.set_mask_transparent()
    await manager.show_dialog("第一步：從資料庫中檢索知識。請在下方輸入框輸入 Query，並按下 Enter 搜尋！", false)
    var current_scene: Node = manager.get_tree().current_scene
    if current_scene:
        var query_bar: Node = current_scene.find_child("QueryBar", true, false)
        if query_bar:
            manager.focus_node(query_bar)

func exit() -> void:
    manager.unfocus()
    var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
    if event_bus != null:
        event_bus.card_drawn.disconnect(_on_card_drawn)

func _on_card_drawn(card_data: Resource) -> void:
    if card_data.get("type") == 2 or card_data.get("type") == 3:
        transitioned.emit("DragData")
