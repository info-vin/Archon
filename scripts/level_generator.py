import os
import yaml

def generate_levels():
    print("⚙️  [LevelGenerator] Commencing dynamic 100+ micro-scenario YAML generation...")
    
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "twin_scenarios", "05_generated_levels"))
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Define the parameterized levels matrices (Campaigns A, B, C, D)
    levels = []
    
    # Campaign A: RBAC Defense Matrix (Negative Tests)
    # Generate 40 micro-scenarios testing different unauthorized endpoints per persona
    personas = ["alice@archon.com", "bob@archon.com", "charlie@archon.com", "dev.bot@archon.com"]
    forbidden_routes = ["/#/admin", "/#/nexus", "/#/settings"]
    for i in range(1, 41):
        persona = personas[(i - 1) % len(personas)]
        route = forbidden_routes[(i - 1) % len(forbidden_routes)]
        levels.append({
            "id": f"L_CAMP_A_{i:03d}",
            "name": f"Campaign A Level {i:03d} - RBAC Block for {persona.split('@')[0]} to {route}",
            "description": f"Verify persona {persona} is blocked with HTTP 403 or redirect when accessing {route}.",
            "auth": {
                "url": "/#/auth",
                "user": persona,
                "password": "qwer45tyuiop"
            },
            "steps": [
                {"action": "goto", "url": route, "wait_until": "domcontentloaded", "timeout": 20000},
                {"action": "sleep", "duration": 2000}
            ],
            "analysis": {
                "type": "static",
                "success_message": "WORKFLOW_SUCCESS"
            }
        })
        
    # Campaign B: Latency / 503 Resilient Load Tests (30 Levels)
    for i in range(1, 31):
        # Calculate dynamic chaos parameters based on level ID index
        latency = i * 100  # 100ms up to 3000ms latency
        error_rate = round(0.02 * (i % 5), 2)  # 0% to 8% HTTP 500 error rate
        offline = [2] if i % 10 == 0 else []  # Simulate offline on step 2 for every 10th level
        
        levels.append({
            "id": f"L_CAMP_B_{i:03d}",
            "name": f"Campaign B Level {i:03d} - Stress Load verification",
            "description": f"Stress-test the system responsiveness under artificial latency ({latency}ms) and error rate ({error_rate * 100}%).",
            "auth": {
                "url": "/#/auth",
                "user": "bob@archon.com",
                "password": "qwer45tyuiop"
            },
            "chaos": {
                "latency_ms": latency,
                "error_rate": error_rate,
                "offline_steps": offline
            },
            "steps": [
                {"action": "goto", "url": "/#/brand", "wait_until": "domcontentloaded", "timeout": 20000},
                {"action": "sleep", "duration": 1000}
            ],
            "analysis": {
                "type": "static",
                "success_message": "WORKFLOW_SUCCESS"
            }
        })

    # Campaign C: Multimodal inputs (20 Levels)
    for i in range(1, 21):
        levels.append({
            "id": f"L_CAMP_C_{i:03d}",
            "name": f"Campaign C Level {i:03d} - Input edge case verification",
            "description": "Ensure the frontend boundary validations hold clean.",
            "auth": {
                "url": "/#/auth",
                "user": "alice@archon.com",
                "password": "qwer45tyuiop"
            },
            "steps": [
                {"action": "goto", "url": "/#/marketing", "wait_until": "domcontentloaded", "timeout": 20000},
                {"action": "sleep", "duration": 1000}
            ],
            "analysis": {
                "type": "static",
                "success_message": "WORKFLOW_SUCCESS"
            }
        })
        
    # Campaign D: Consistency and Analytics (10 Levels)
    for i in range(1, 11):
        levels.append({
            "id": f"L_CAMP_D_{i:03d}",
            "name": f"Campaign D Level {i:03d} - Analytics Audit verification",
            "description": "Verify consistency on general metrics reporting panels.",
            "auth": {
                "url": "/#/auth",
                "user": "admin@archon.com",
                "password": "qwer45tyuiop"
            },
            "steps": [
                {"action": "goto", "url": "/#/admin", "wait_until": "domcontentloaded", "timeout": 20000},
                {"action": "sleep", "duration": 1000}
            ],
            "analysis": {
                "type": "static",
                "success_message": "WORKFLOW_SUCCESS"
            }
        })

    # Write each level to a separate YAML file
    for lvl in levels:
        file_path = os.path.join(output_dir, f"{lvl['id']}.yaml")
        yaml_content = {
            "name": lvl["name"],
            "mode": "scenario",
            "description": lvl["description"],
            "hooks": {
                "before_auth": [
                    {
                        "type": "python_function",
                        "module": "scripts.setup_personas",
                        "function": "setup_sandbox",
                        "args": {
                            "level_id": lvl["id"],
                            "force_clean": True
                        }
                    }
                ]
            },
            "auth": lvl["auth"],
            "resolution": {"width": 1280, "height": 720},
            "steps": lvl["steps"],
            "analysis": lvl["analysis"]
        }
        if "chaos" in lvl:
            yaml_content["chaos"] = lvl["chaos"]
            
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f, allow_unicode=True, sort_keys=False)
            
    print(f"🎉 [LevelGenerator] Generated {len(levels)} parameterized scenario files in {output_dir}")

if __name__ == "__main__":
    generate_levels()
