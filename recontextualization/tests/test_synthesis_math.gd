extends SceneTree

func _init():
    run_monte_carlo()

func calculate_success_rate(level: int, catalyst: String) -> float:
    var bsr = max(0.10, 1.0 - (level * 0.15))
    var bonus = 0.0
    if catalyst == "data_core_s":
        bonus = 0.5
    elif catalyst == "data_core_a":
        bonus = 0.2
        
    return min(1.0, bsr + bonus)

func run_monte_carlo() -> void:
    print("--- Running Synthesis Math Monte Carlo (2000 iterations) ---")
    
    var sim_count = 2000
    var levels_to_test = [1, 3, 5, 8]
    var catalysts = ["none", "data_core_a", "data_core_s"]
    
    for level in levels_to_test:
        for catalyst in catalysts:
            var rate = calculate_success_rate(level, catalyst)
            var successes = 0
            
            # Run simulation
            for i in range(sim_count):
                if randf() <= rate:
                    successes += 1
                    
            var actual_rate = float(successes) / float(sim_count)
            print("Lv%d -> Lv%d | Catalyst: %s | Expected: %.1f%% | Actual: %.1f%%" % [
                level, level + 1, catalyst.pad_right(12), rate * 100.0, actual_rate * 100.0
            ])
            
            # Assert that actual rate is within 3% margin of error
            assert(abs(actual_rate - rate) < 0.03, "Monte Carlo variance too high, expected approx %.2f, got %.2f" % [rate, actual_rate])
            
    print("--- Monte Carlo Simulation Complete ---")
    quit()
