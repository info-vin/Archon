extends ReferenceRect

@export var pulse_speed: float = 2.0

func _process(delta: float) -> void:
    modulate.a = (sin(Time.get_ticks_msec() / 1000.0 * PI * pulse_speed) + 1.0) / 2.0
