extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    # Connect to the event bus to listen for cards being drawn (which happens after search)
    Engine.get_singleton("EventBus").card_drawn.connect(_on_card_drawn)
    
    manager.set_mask_transparent()
    await manager.show_dialog("第一步：從資料庫中檢索知識。請在下方輸入框輸入 Query，並點擊『關鍵字搜索』卡牌！", false)

func exit() -> void:
    Engine.get_singleton("EventBus").card_drawn.disconnect(_on_card_drawn)

func _on_card_drawn(card_data: Resource) -> void:
    # A card was successfully retrieved. Move to next state.
    transitioned.emit("DragData")
