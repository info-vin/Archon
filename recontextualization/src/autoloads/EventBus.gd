extends Node

# UI and Action Signals
signal card_drawn(card: Resource)
signal request_play_card(card: Resource)
signal card_played(card: Resource)
signal deck_shuffled()
signal game_over(is_victory: bool)

# RAG Crisis Signals
signal timeout_sla_tick(remaining_seconds: int)
signal rate_limit_attack_triggered(reduced_ap: int)
signal db_poisoning_escalated(noise_ratio: float)
