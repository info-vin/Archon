extends RefCounted
class_name MiniTest

var tests_passed: int = 0
var tests_failed: int = 0
var tree: SceneTree = null

func assert_eq(actual, expected, message: String = "") -> void:
	if actual == expected:
		tests_passed += 1
		print("  🟢 [PASS] ", message)
	else:
		tests_failed += 1
		push_error("  🔴 [FAIL] ", message, " | Expected: ", expected, " | Got: ", actual)

func assert_not_null(actual, message: String = "") -> void:
	if actual != null:
		tests_passed += 1
		print("  🟢 [PASS] ", message)
	else:
		tests_failed += 1
		push_error("  🔴 [FAIL] ", message, " | Expected not null")

func assert_true(actual: bool, message: String = "") -> void:
	if actual == true:
		tests_passed += 1
		print("  🟢 [PASS] ", message)
	else:
		tests_failed += 1
		push_error("  🔴 [FAIL] ", message, " | Expected: true | Got: false")

func assert_false(actual: bool, message: String = "") -> void:
	if actual == false:
		tests_passed += 1
		print("  🟢 [PASS] ", message)
	else:
		tests_failed += 1
		push_error("  🔴 [FAIL] ", message, " | Expected: false | Got: true")

# 這個函數會在繼承此腳本的測試檔中被呼叫
func run_test_suite() -> void:
	print("\n========== RUNNING TESTS ==========")
	tests_passed = 0
	tests_failed = 0
	
	# 尋找所有以 "test_" 開頭的函數並執行
	for method in get_method_list():
		if method.name.begins_with("test_"):
			# 清理 savegame 防止跨測試狀態污染
			if FileAccess.file_exists("user://savegame.json"):
				DirAccess.remove_absolute("user://savegame.json")
			
			print("\n➡️ Running: ", method.name)
			await call(method.name)
			
			if FileAccess.file_exists("user://savegame.json"):
				DirAccess.remove_absolute("user://savegame.json")
			
	print("\n========== RESULTS ==========")
	if tests_failed == 0:
		print("✅ ALL TESTS PASSED (", tests_passed, " assertions)")
	else:
		push_error("❌ TESTS FAILED! Passed: ", tests_passed, " | Failed: ", tests_failed)
	print("===================================\n")
