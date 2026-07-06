extends Control
class_name AgentCompanion

@export var rich_text_label: RichTextLabel
@export var typewriter_timer: Timer

var _typing_queue: Array = []
var _is_typing: bool = false
var _current_text: String = ""
var _char_index: int = 0

func _ready() -> void:
    if typewriter_timer:
        typewriter_timer.timeout.connect(_on_typewriter_step)
    
    # Initial greeting via translation key equivalent or BBCode
    push_message("[color=green]Agentic RAG Core initialized. Waiting for uplink...[/color]")

func push_message(msg: String) -> void:
    _typing_queue.append(msg)
    if not _is_typing:
        _start_next_message()

func _start_next_message() -> void:
    if _typing_queue.is_empty():
        _is_typing = false
        return
        
    _is_typing = true
    _current_text = _typing_queue.pop_front()
    _char_index = 0
    if rich_text_label:
        rich_text_label.text += "\n> "
    if typewriter_timer:
        typewriter_timer.start()

func _on_typewriter_step() -> void:
    if _char_index < _current_text.length():
        if rich_text_label:
            rich_text_label.text += _current_text[_char_index]
        _char_index += 1
    else:
        if typewriter_timer:
            typewriter_timer.stop()
        _start_next_message()

var ChaosEventPool = preload("res://src/models/events/ChaosEventPool.gd")
var CombatJuice = preload("res://src/views/components/CombatJuice.gd")

func trigger_chaos_event(event_id: String) -> void:
    if ChaosEventPool:
        var ev = ChaosEventPool.get_event(event_id)
        if ev:
            push_message("[color=red]" + ev["dialogue"] + "[/color]")
            
            if CombatJuice:
                CombatJuice.glitch_effect(self)
