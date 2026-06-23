import re

print("Refactoring Main.gd and Main.tscn...")

# Read Main.gd
with open("archon-agency-tycoon/Scripts/Main.gd", "r") as f:
    main_gd = f.read()

# Update onready paths in Main.gd
main_gd = re.sub(r'@onready var minimap_container: Control = \$VBox/HBoxMain/RightPanel/VBox/MinimapContainer', '@onready var minimap_container: Control = $UILayer/UI/RightPanel/VBox/MinimapContainer', main_gd)
main_gd = re.sub(r'@onready var ticker: RichTextLabel = \$VBox/TopBar/HBox/TickerLabel', '@onready var ticker: RichTextLabel = $UILayer/UI/TopBar/HBox/TickerLabel', main_gd)
main_gd = re.sub(r'@onready var lang_button: Button = \$VBox/TopBar/HBox/LangButton', '@onready var lang_button: Button = $UILayer/UI/TopBar/HBox/LangButton', main_gd)
main_gd = re.sub(r'@onready var jukebox_button: Button = \$VBox/TopBar/HBox/JukeboxButton', '@onready var jukebox_button: Button = $UILayer/UI/TopBar/HBox/JukeboxButton', main_gd)
main_gd = re.sub(r'@onready var task_container: HBoxContainer = \$VBox/BottomBar/VBox/TaskContainer', '@onready var task_container: HBoxContainer = $UILayer/UI/BottomBar/VBox/TaskContainer', main_gd)

# Office rooms are now Node2D under World/Rooms
main_gd = re.sub(r'@onready var dev_room_label: Label = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/DevRoom/Label', '@onready var dev_room_label: Label = $World/Rooms/DevRoom/Label', main_gd)
main_gd = re.sub(r'@onready var sales_room_label: Label = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/SalesRoom/Label', '@onready var sales_room_label: Label = $World/Rooms/SalesRoom/Label', main_gd)
main_gd = re.sub(r'@onready var qa_room_label: Label = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/QARoom/Label', '@onready var qa_room_label: Label = $World/Rooms/QARoom/Label', main_gd)
main_gd = re.sub(r'@onready var break_room_label: Label = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/BreakRoom/Label', '@onready var break_room_label: Label = $World/Rooms/BreakRoom/Label', main_gd)

# Room types change from PanelContainer to Node2D
main_gd = re.sub(r'@onready var dev_room: PanelContainer = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/DevRoom', '@onready var dev_room: Node2D = $World/Rooms/DevRoom', main_gd)
main_gd = re.sub(r'@onready var sales_room: PanelContainer = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/SalesRoom', '@onready var sales_room: Node2D = $World/Rooms/SalesRoom', main_gd)
main_gd = re.sub(r'@onready var qa_room: PanelContainer = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/QARoom', '@onready var qa_room: Node2D = $World/Rooms/QARoom', main_gd)
main_gd = re.sub(r'@onready var break_room: PanelContainer = \$VBox/HBoxMain/GameArea/Building/OfficeGrid/BreakRoom', '@onready var break_room: Node2D = $World/Rooms/BreakRoom', main_gd)

main_gd = re.sub(r'\$VBox/BottomBar/VBox/ActionHBox/RecruitBtn', '$UILayer/UI/BottomBar/VBox/ActionHBox/RecruitBtn', main_gd)
main_gd = re.sub(r'\$VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn', '$UILayer/UI/BottomBar/VBox/ActionHBox/ExpandRoomBtn', main_gd)
main_gd = re.sub(r'\$VBox/BottomBar/VBox/ActionHBox/SaveBtn', '$UILayer/UI/BottomBar/VBox/ActionHBox/SaveBtn', main_gd)
main_gd = re.sub(r'"VBox/HBoxMain/RightPanel/VBox/EventLog"', '"UILayer/UI/RightPanel/VBox/EventLog"', main_gd)

# Remove office_grid references since we are moving away from grid container
main_gd = re.sub(r'@onready var office_grid: GridContainer = \$VBox/HBoxMain/GameArea/Building/OfficeGrid\n', '@onready var office_grid: Node2D = $World/Rooms\n', main_gd)

with open("archon-agency-tycoon/Scripts/Main.gd", "w") as f:
    f.write(main_gd)

print("Main.gd updated!")
