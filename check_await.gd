extends SceneTree
func _init():
	test()
func test():
	print("Start")
	await my_coroutine()
	print("End")
	quit()
func my_coroutine() -> void:
	print("Inside coroutine")
	await create_timer(1.0).timeout
	print("Inside coroutine end")
