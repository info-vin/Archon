extends Node

signal tick_updated(tick_count: int, funds: int, reputation: int)
signal agent_spawned(agent_id: int, target_room: String)
signal task_generated(task_id: int, task_name: String, ticks: int, reward: int)
