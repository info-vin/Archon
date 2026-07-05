extends RefCounted

## Applies a damage shake effect to a UI Control node.
static func shake_ui_element(node: Control, intensity: float = 10.0, duration: float = 0.2) -> Tween:
	var tween = node.create_tween()
	var original_pos = node.position
	tween.tween_property(node, "position", original_pos + Vector2(intensity, 0), duration * 0.25)
	tween.tween_property(node, "position", original_pos - Vector2(intensity, 0), duration * 0.25)
	tween.tween_property(node, "position", original_pos + Vector2(intensity/2.0, 0), duration * 0.25)
	tween.tween_property(node, "position", original_pos, duration * 0.25)
	return tween

## Flashes a UI element red and shakes it.
static func damage_flash_and_shake(node: Control) -> Tween:
	node.modulate = Color.RED
	var tween = shake_ui_element(node, 10.0, 0.2)
	tween.parallel().tween_property(node, "modulate", Color.WHITE, 0.3)
	return tween

## Creates a pulsing warning color.
static func warning_pulse(node: CanvasItem, time_msec: float, speed: float = 150.0) -> void:
	var pulse = (sin(time_msec / speed) + 1.0) / 2.0
	node.modulate = Color.WHITE.lerp(Color.RED, pulse)

## Flashes an element's alpha.
static func flash_alpha(node: CanvasItem) -> Tween:
	var tween = node.create_tween()
	tween.tween_property(node, "modulate:a", 0.0, 0.2)
	tween.tween_property(node, "modulate:a", 1.0, 0.2)
	return tween
