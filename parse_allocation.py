# parse_allocation.py
import re
import json

def parse_allocation_plan(text):
    parsed = {"phases": []}
    current_phase = None
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        # Match phase headers (e.g., "**Phase 1: Planning and Analysis**")
        phase_match = re.match(r'\*\*Phase (\d+): (.+)\*\*', line)
        if phase_match:
            current_phase = {
                "phase_number": int(phase_match.group(1)),
                "phase_name": phase_match.group(2),
                "tasks": []
            }
            parsed["phases"].append(current_phase)
            continue
        
        # Match task lines (e.g., "* Task 1.1: Define project scope...")
        task_match = re.match(r'\* Task (\d+\.\d+): (.+)', line)
        if task_match and current_phase:
            task = {
                "task_id": task_match.group(1),
                "task_name": task_match.group(2),
                "assigned_to": [],
                "duration": None,
                "resources": []
            }
            current_phase["tasks"].append(task)
            continue
        
        # Match assignment lines (e.g., "+ Assigned to: Rachel (Project Manager)...")
        assigned_match = re.match(r'\+ Assigned to: (.+)', line)
        if assigned_match and current_phase and current_phase["tasks"]:
            # Get the last added task
            current_task = current_phase["tasks"][-1]
            # Split multiple assignees
            assignees = [a.strip() for a in assigned_match.group(1).split(' and ')]
            current_task["assigned_to"].extend(assignees)
            continue
        
        # Match duration lines (e.g., "+ Estimated time: 2 days")
        duration_match = re.match(r'\+ Estimated time: (\d+ days?)', line)
        if duration_match and current_phase and current_phase["tasks"]:
            current_task = current_phase["tasks"][-1]
            current_task["duration"] = duration_match.group(1)
    
    print("Parsed JSON Object:", json.dumps(parsed, indent=2))
    
    return parsed