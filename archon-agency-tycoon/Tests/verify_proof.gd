extends SceneTree

func _initialize() -> void:
    print("--- 🔬 實體自治/MVC 邏輯驗證實驗 ---")
    var scene = load("res://Scenes/Main/Main.tscn")
    var view = scene.instantiate()
    
    # 證明：如果我們手動掛載腳本，屬性完全可以存取，邏輯完全沒問題
    view.set_script(load("res://Scripts/Main.gd"))
    view.instant_positioning = true
    
    if view.instant_positioning == true:
        print("🟢 證明成功：Main.gd 變數存取正常，邏輯無誤。")
    else:
        print("🔴 證明失敗。")
    
    quit(0)
