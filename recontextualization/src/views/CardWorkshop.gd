extends Control
class_name CardWorkshop

# --- Synthesis Constants ---
const CATALYST_S = "data_core_s"
const CATALYST_A = "data_core_a"
const CATALYST_S_BONUS = 0.5
const CATALYST_A_BONUS = 0.2
const COGNITIVE_BONUS_MULT = 0.01
const COGNITIVE_BONUS_MAX = 0.20
# ---------------------------

# UI References (To be assigned in Editor)
@export var inventory_container: VBoxContainer
@export var slot_1: TextureRect
@export var slot_2: TextureRect
@export var slot_3: TextureRect
@export var catalyst_slot: TextureRect
@export var synthesize_btn: Button
@export var status_label: Label

var current_cards_in_furnace: Array = []
var current_catalyst: String = "none"

func _ready():
    synthesize_btn.pressed.connect(_on_synthesize_pressed)
    refresh_inventory_ui()

func refresh_inventory_ui() -> void:
    # Clear old list
    for child in inventory_container.get_children():
        child.queue_free()
        
    var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
    if not sm:
        return
        
    for card_data in sm.player_inventory:
        var btn = Button.new()
        btn.text = "%s Lv.%d" % [card_data.get("base_id", "Unknown"), card_data.get("level", 1)]
        btn.pressed.connect(func(): _on_inventory_card_clicked(card_data))
        inventory_container.add_child(btn)

func _on_inventory_card_clicked(card_data: Dictionary) -> void:
    if current_cards_in_furnace.size() < 3:
        # Must be same base_id and level to synthesize
        if current_cards_in_furnace.size() > 0:
            var first_card = current_cards_in_furnace[0]
            if first_card["base_id"] != card_data["base_id"] or first_card["level"] != card_data["level"]:
                status_label.text = "Error: Must use identical cards!"
                return
                
        current_cards_in_furnace.append(card_data)
        _update_furnace_ui()

func _update_furnace_ui() -> void:
    status_label.text = "Furnace: %d/3 Cards" % current_cards_in_furnace.size()
    if current_cards_in_furnace.size() == 3:
        var target_level = current_cards_in_furnace[0]["level"]
        var rate = _calculate_success_rate(target_level, current_catalyst)
        status_label.text = "Ready! Success Rate: %.1f%%" % (rate * 100.0)

func _calculate_success_rate(level: int, catalyst: String) -> float:
    var bsr = max(0.10, 1.0 - (level * 0.15))
    var bonus = 0.0
    if catalyst == CATALYST_S:
        bonus = CATALYST_S_BONUS
    elif catalyst == CATALYST_A:
        bonus = CATALYST_A_BONUS
        
    var level_bonus = 0.0
    var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
    if sm:
        level_bonus = min(COGNITIVE_BONUS_MAX, sm.cognitive_level * COGNITIVE_BONUS_MULT)
        
    return min(1.0, bsr + bonus + level_bonus)

func _on_synthesize_pressed() -> void:
    if current_cards_in_furnace.size() < 3:
        return
        
    var target_level = current_cards_in_furnace[0]["level"]
    var base_id = current_cards_in_furnace[0]["base_id"]
    var rate = _calculate_success_rate(target_level, current_catalyst)
    
    var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
    if sm:
        # Deduct catalyst
        if current_catalyst != "none":
            if sm.material_inventory.has(current_catalyst) and sm.material_inventory[current_catalyst] > 0:
                sm.material_inventory[current_catalyst] -= 1
            else:
                status_label.text = "Error: Catalyst missing!"
                return

        # Safely remove the 3 exact cards from inventory
        for c in current_cards_in_furnace:
            var idx = sm.player_inventory.find(c)
            if idx != -1:
                sm.player_inventory.remove_at(idx)
            
        if randf() <= rate:
            status_label.text = "Synthesis SUCCESS!"
            sm.player_inventory.append({"base_id": base_id, "level": target_level + 1})
            # Play success animation here
        else:
            status_label.text = "Synthesis FAILED... Yielded scrap."
            sm.material_inventory["scrap"] = sm.material_inventory.get("scrap", 0) + 1
            # Play failure/shatter animation here
            
        sm.save_progress()
        
    current_cards_in_furnace.clear()
    current_catalyst = "none"
    refresh_inventory_ui()
    _update_furnace_ui()
