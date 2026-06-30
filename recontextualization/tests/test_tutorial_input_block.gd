extends SceneTree

func _init():
	call_deferred("run_tests")

func run_tests():
	print("Running test_tutorial_input_block...")
	var tests_passed = 0
	var tests_failed = 0
	
	var overlay = preload("res://src/views/tutorial/TutorialOverlay.tscn").instantiate()
	root.add_child(overlay)
	
	# Test 1: Initial state
	if overlay.dialog_box.mouse_filter == Control.MOUSE_FILTER_IGNORE:
		print("✅ DialogBox mouse_filter is IGNORE (2).")
		tests_passed += 1
	else:
		print("❌ DialogBox mouse_filter is not IGNORE, it is: ", overlay.dialog_box.mouse_filter)
		tests_failed += 1
		
	# Test 2: set_mask_transparent DOES NOT hide dialog box (it should remain visible for reading!)
	overlay.show_dialog("Test", false)
	overlay.set_mask_transparent()
	
	if overlay.mask_rect.mouse_filter == Control.MOUSE_FILTER_IGNORE:
		print("✅ MaskRect mouse_filter is IGNORE (2) when transparent.")
		tests_passed += 1
	else:
		print("❌ MaskRect mouse_filter is not IGNORE when transparent.")
		tests_failed += 1
		
	if overlay.dialog_box.visible:
		print("✅ DialogBox is still visible after set_mask_transparent() (allows reading during action).")
		tests_passed += 1
	else:
		print("❌ DialogBox is hidden after set_mask_transparent().")
		tests_failed += 1

	# Test 3: Dialog position is not at the bottom
	var box_rect = overlay.dialog_box.get_rect()
	if box_rect.position.y < 200:
		print("✅ DialogBox is positioned at the top/middle (Y=", box_rect.position.y, "), away from hand container.")
		tests_passed += 1
	else:
		print("❌ DialogBox is positioned too low (Y=", box_rect.position.y, "), might block cards.")
		tests_failed += 1
		
	# Test 4: Requires click flag
	if overlay.requires_click == false:
		print("✅ requires_click is correctly set to false.")
		tests_passed += 1
	else:
		print("❌ requires_click is true despite wait_for_click=false.")
		tests_failed += 1
		
	if tests_failed > 0:
		print("❌ Some tests failed.")
		quit(1)
	else:
		print("✅ All input block tests passed successfully.")
		quit(0)
