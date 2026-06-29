extends Node
class_name EventQueue

var _queue: Array[Callable] = []
var _is_processing: bool = false

## Adds an animation coroutine to the queue and starts processing if idle.
func add_animation(anim: Callable):
	_queue.append(anim)
	if not _is_processing:
		_process_queue()

func _process_queue():
	_is_processing = true
	while not _queue.is_empty():
		var anim = _queue.pop_front()
		# Execute the coroutine and await its completion.
		await anim.call()
	_is_processing = false

## Utility method to wait for a specific duration (in seconds)
func wait(duration: float) -> Callable:
	return func():
		await get_tree().create_timer(duration).timeout
