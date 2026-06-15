import os
import sys
import time

# --- Config ---
GRID_W, GRID_H = 12, 8
MAX_CONTEXT = 5
KNN_RADIUS = 2

# --- Init State ---
def reset_state():
    return {
        "Q": [1, 1], # Query (Player)
        "L": [10, 6], # LLM Portal (Goal)
        "T": [[4, 2], [8, 1], [3, 6]], # Target Chunks (Good)
        "F": [{"pos": [5, 4], "awake": False}, {"pos": [9, 4], "awake": False}], # False Positives (Bad)
        "walls": [[3, 1], [3, 2], [3, 3], [7, 5], [7, 6]],
        "context": [], # List of 'T' or 'F'
        "status": "PLAYING",
        "msg": "Find [T]argets, avoid [F]alse positives, reach [L]LM."
    }

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def draw_grid(state):
    grid = [["." for _ in range(GRID_W)] for _ in range(GRID_H)]
    
    for w in state["walls"]: grid[w[1]][w[0]] = "#"
    for t in state["T"]: grid[t[1]][t[0]] = "T"
    for f in state["F"]: 
        char = "F" if f["awake"] else "f"
        grid[f["pos"][1]][f["pos"][0]] = char
    
    grid[state["L"][1]][state["L"][0]] = "L"
    grid[state["Q"][1]][state["Q"][0]] = "Q"
    
    output = []
    output.append("="*30)
    for row in grid:
        output.append(" ".join(row))
    output.append("-" * 30)
    
    ctx_display = "[" + ", ".join(state["context"]) + "]"
    output.append(f"Context Window: {ctx_display} ({len(state['context'])}/{MAX_CONTEXT} Tokens)")
    output.append(f"Status: {state['status']}")
    output.append(f"Msg: {state['msg']}")
    output.append("="*30)
    return "\n".join(output)

def process_turn(state, move_cmd):
    if state["status"] != "PLAYING": return
    
    dx, dy = 0, 0
    if move_cmd == 'w': dy = -1
    elif move_cmd == 's': dy = 1
    elif move_cmd == 'a': dx = -1
    elif move_cmd == 'd': dx = 1
    
    new_q = [state["Q"][0] + dx, state["Q"][1] + dy]
    
    # Check Wall / Bounds
    if 0 <= new_q[0] < GRID_W and 0 <= new_q[1] < GRID_H and new_q not in state["walls"]:
        state["Q"] = new_q
    
    # 1. Collect Target (T)
    if state["Q"] in state["T"]:
        state["T"].remove(state["Q"])
        state["context"].append("T")
        state["msg"] = "Loaded useful Chunk into Context!"
    
    # 2. Check LLM Portal (L)
    if state["Q"] == state["L"]:
        t_count = state["context"].count("T")
        f_count = state["context"].count("F")
        if t_count == 0:
            state["status"] = "FAILED (Empty Response)"
            state["msg"] = "LLM Generation Failed: No useful context provided."
        elif f_count > t_count:
            state["status"] = "FAILED (Hallucination)"
            state["msg"] = f"LLM Hallucinated! Too much noise ({f_count}F vs {t_count}T)."
        else:
            state["status"] = "VICTORY"
            state["msg"] = f"Accurate Generation! Context was clean enough."
        return

    # 3. Check Context Limit
    if len(state["context"]) > MAX_CONTEXT:
        state["status"] = "FAILED (OOM)"
        state["msg"] = "Token Limit Exceeded! System crashed."
        return
        
    # 4. Process Enemies (F) - KNN Retrieval Logic
    for f in state["F"]:
        dist = manhattan(state["Q"], f["pos"])
        
        # Wake up if close (Semantic Similarity match)
        if not f["awake"] and dist <= KNN_RADIUS:
            f["awake"] = True
            state["msg"] = "WARNING: False Positive retrieved! It's tracking you!"
            
        # Move towards Q if awake
        if f["awake"]:
            # Simple chase logic
            fdx = 1 if state["Q"][0] > f["pos"][0] else (-1 if state["Q"][0] < f["pos"][0] else 0)
            fdy = 1 if state["Q"][1] > f["pos"][1] else (-1 if state["Q"][1] < f["pos"][1] else 0)
            
            next_f = [f["pos"][0] + fdx, f["pos"][1]]
            if next_f not in state["walls"] and next_f != state["L"]:
                f["pos"] = next_f
            else:
                next_f = [f["pos"][0], f["pos"][1] + fdy]
                if next_f not in state["walls"] and next_f != state["L"]:
                    f["pos"] = next_f
                    
            # Check Collision with Q
            if f["pos"] == state["Q"]:
                state["context"].append("F")
                f["awake"] = False # Absorbed
                f["pos"] = [-1, -1] # Remove from board
                state["msg"] = "Noise absorbed into Context Window!"

def run_simulation(commands):
    print("--- STARTING RAG ASCII SIMULATION ---")
    state = reset_state()
    print(draw_grid(state))
    for i, cmd in enumerate(commands):
        print(f"\n[Turn {i+1}] Input: {cmd}")
        process_turn(state, cmd)
        print(draw_grid(state))
        if state["status"] != "PLAYING":
            break
    print("--- SIMULATION END ---")

def run_interactive():
    state = reset_state()
    while state["status"] == "PLAYING":
        os.system('clear' if os.name == 'posix' else 'cls')
        print(draw_grid(state))
        cmd = input("Move (w/a/s/d): ").strip().lower()
        if cmd in ['w', 'a', 's', 'd']:
            process_turn(state, cmd)
        elif cmd == 'q':
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        run_interactive()
    else:
        print("\n\n>>> SCENARIO 1: Semantic Hallucination (Too much noise)")
        # Grab T at [4,2], then get caught by F at [5,4] and F at [9,4], then run to L [10,6]
        # From [1,1]: s, s, s, d, d, d, w, w (Get T at 4,2)
        # s, s, d, d (Hit F at 5,4)
        # d, d, d, d (Hit F at 9,4)
        # s, s, d (Reach L at 10,6)
        commands_fail = ['s','s','s','d','d','d','w','w', 's','s','d','d', 'd','d','d','d', 's','s','d'] 
        run_simulation(commands_fail)
        
        print("\n\n>>> SCENARIO 2: Clean RAG Generation (Success)")
        # Dodge Fs, grab T at [3,6] and T at [8,1], then go to L
        # This proves the mathematical win state.
        commands_success = ['s','s','s','s','s','d','d', 'd','d','w','w','w','w','w','d','d','d','d','d','s','s','s','s','s']
        run_simulation(commands_success)
