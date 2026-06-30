extends SceneTree
signal my_sig
func _init():
	test()
func test():
	print("Start")
	call_deferred("emit_sig")
	await my_coroutine()
	print("End")
	quit()
func my_coroutine() -> void:
	print("Inside coroutine")
	await my_sig
	print("Inside coroutine end")
func emit_sig():
	print("Emitting sig")
	my_sig.emit()
