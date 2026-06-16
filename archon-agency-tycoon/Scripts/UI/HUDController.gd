extends Node
class_name HUDController

var main_node: Control

func initialize(p_main_node: Control) -> void:
	main_node = p_main_node

func update_static_labels() -> void:
	if not main_node: return
	
	# Update room labels
	if main_node.dev_room_label: main_node.dev_room_label.text = tr("ROOM_DEV")
	if main_node.sales_room_label: main_node.sales_room_label.text = tr("ROOM_SALES")
	if main_node.qa_room_label: main_node.qa_room_label.text = tr("ROOM_QA")
	if main_node.break_room_label: main_node.break_room_label.text = tr("ROOM_BREAK")
	
	# Right panel headers
	var event_log_lbl = main_node.get_node_or_null("VBox/HBoxMain/RightPanel/VBox/EventLogLabel")
	if event_log_lbl: event_log_lbl.text = tr("UI_EVENT_LOG")
	
	var agent_status_lbl = main_node.get_node_or_null("VBox/HBoxMain/RightPanel/VBox/AgentStatusLabel")
	if agent_status_lbl: agent_status_lbl.text = tr("UI_AGENT_STATUS")
	
	var minimap_lbl = main_node.get_node_or_null("VBox/HBoxMain/RightPanel/VBox/MinimapLabel")
	if minimap_lbl: minimap_lbl.text = tr("UI_MINIMAP")
	
	# Action buttons
	var tasks_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/TasksBtn")
	if tasks_btn: tasks_btn.text = tr("UI_BACKLOG")
	
	var save_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/SaveBtn")
	if save_btn: save_btn.text = tr("UI_SAVE")
	
	var recruit_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/RecruitBtn")
	if recruit_btn: recruit_btn.text = tr("UI_CHARACTER_CREATOR")
	
	var expand_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn")
	if expand_btn: expand_btn.text = tr("UI_EXPAND_ROOM")

func update_ticker(tick_count: int, funds: int, reputation: int) -> void:
	if not main_node or not main_node.ticker: return
	
	var f_color = "#39ff14" if funds > 0 else "#ff003c"
	var r_color = "#39ff14" if reputation > 50 else "#ff003c"
	main_node.ticker.text = "[color=#888888]ARCHON CORP | TICK:[/color] [color=#ffffff]%d[/color] [color=#888888]| %s:[/color] [color=%s]$%d[/color] [color=#888888]| %s:[/color] [color=%s]%d[/color]" % [
		tick_count, 
		tr("UI_FUNDS"), f_color, funds,
		tr("UI_REP"), r_color, reputation
	]
