extends "res://src/managers/tutorial/TutorialState.gd"

func enter() -> void:
    manager.set_mask_dark()
    
    # Show welcome messages
    await manager.show_dialog("菜鳥，聽好了！系統快崩潰了，SLA (時間) 正在瘋狂倒數。")
    await manager.show_dialog("身為 RAG 工程師，你必須精準地將正確的資料晶片交付給 LLM。")
    await manager.show_dialog("看到畫面上方的『Crisis HP』了嗎？想辦法把它扣到 0！")
    
    transitioned.emit("Search")
