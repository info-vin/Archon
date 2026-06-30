extends SceneTree

signal my_sig

func _init():
	call_deferred("run_test")

func run_test():
	print("Start time: ", Time.get_ticks_msec())
	call_deferred("delayed_emit")
	await my_coroutine()
	print("End time: ", Time.get_ticks_msec())
	quit()

func my_coroutine() -> void:
	await my_sig

func delayed_emit():
	await create_timer(1.0).timeout
	my_sig.emit()
