extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    manager.set_mask_transparent()
    await manager.show_dialog("幹得好！乾淨的資料能保護系統不產生幻覺。\n現在點擊『交付 LLM (Deliver)』按鈕，結算傷害吧！", false)
    var deliver_btn = manager.get_tree().current_scene.find_child("DeliverButton", true, false)
    if deliver_btn:
        manager.focus_node(deliver_btn)

func update(_delta: float) -> void:
    # We can check if the player delivered. GameState handles the actual delivery logic.
    # In tutorial we could just wait for GameState to emit an event, or we can just hook into the deliver button.
    # Since GameState doesn't explicitly emit "delivered" unless crisis is defeated, we can just listen to crisis_hp_changed or similar.
    # Actually, GameState deducts crisis hp. Let's poll for crisis_hp change.
    if GameState.crisis_hp < GameState.max_crisis_hp:
        transitioned.emit("End")
        set_process(false)

func exit() -> void:
    manager.unfocus()
    manager.show_dialog("防禦成功！現在你已經了解基礎了，去接下你的任務吧！", true)
