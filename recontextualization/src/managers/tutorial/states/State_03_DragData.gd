extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    Engine.get_singleton("EventBus").card_played.connect(_on_card_played)
    
    manager.set_mask_transparent()
    await manager.show_dialog("很好！你抽出了晶片。\n現在，按住『綠色』的高相似度資料晶片，將它『拖曳 (Drag)』到中央的 Play Area！", false)

func exit() -> void:
    Engine.get_singleton("EventBus").card_played.disconnect(_on_card_played)

func _on_card_played(card_data: Resource) -> void:
    if card_data.get("type") == 2:
        # Successfully dragged a data card
        transitioned.emit("Deliver")
