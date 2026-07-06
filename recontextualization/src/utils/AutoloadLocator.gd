class_name AutoloadLocator
extends RefCounted

## 為無頭單元測試 (Headless Tests) 與真實遊戲環境提供統一的單例 (Singleton) 獲取介面。
## 在真實遊戲中，Godot 會將 Autoload 掛載至 /root/ 下。
## 但在 HeadlessRunner.gd 中，我們為了效能並未將所有腳本加入 SceneTree，
## 而是使用了 Engine.register_singleton() 強行註冊在 C++ 底層。
## 此工具類別封裝了兩者的差異，提供簡潔易讀的 API 替換累贅的三元運算子。
static func get_service(tree: SceneTree, singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if tree != null:
		return tree.root.get_node_or_null(singleton_name)
	return null
