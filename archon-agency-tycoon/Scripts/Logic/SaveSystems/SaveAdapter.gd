extends RefCounted
class_name SaveAdapter

# Abstract interface for saving and loading game data.
# This allows swapping between local storage and cloud (Supabase) seamlessly.

func save_data(data: Dictionary) -> bool:
    push_error("SaveAdapter is an abstract class. Implement save_data().")
    return false

func load_data() -> Dictionary:
    push_error("SaveAdapter is an abstract class. Implement load_data().")
    return {}
