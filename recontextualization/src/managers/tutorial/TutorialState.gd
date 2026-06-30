class_name TutorialState
extends Node

signal transitioned(new_state_name)

var manager: Node

func setup(_manager: Node) -> void:
    self.manager = _manager

func enter() -> void:
    pass

func exit() -> void:
    pass

func update(_delta: float) -> void:
    pass
