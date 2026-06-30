extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    # Connect to the event bus to listen for cards being drawn (which happens after search)
    var event_bus = get_node_or_null("/root/EventBus")
    if event_bus != null:
        event_bus.card_drawn.connect(_on_card_drawn)
    
    manager.set_mask_transparent()
    await manager.show_dialog("第一步：從資料庫中檢索知識。請在下方輸入框輸入 Query，並點擊『關鍵字搜索』卡牌！", false)

func exit() -> void:
    var event_bus = get_node_or_null("/root/EventBus")
    if event_bus != null:
        event_bus.card_drawn.disconnect(_on_card_drawn)

func _on_card_drawn(card_data: Resource) -> void:
    if card_data.get("type") == 2 or card_data.get("type") == 3:
        transitioned.emit("DragData")
