import re

def parse_allocation_plan(text):
    """Parse the allocation plan text into a structured format compatible with app.py."""
    
    # Initialize the result structure
    result = {
        "phases": []
    }
    
    # Strip markdown code blocks if present
    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text[3:-3].strip()
    
    # Split the text into lines
    lines = text.strip().split('\n')
    
    current_phase = None
    current_task = None
    in_task_section = False
    
    # Process each line
    for line in lines:
        line = line.strip()
        
        # Skip empty lines or markdown separator lines
        if not line or line.startswith('---'):
            continue
        
        # Check if it's a phase header - try multiple patterns
        phase_match = re.match(r'^##?\s*Phase\s*(\d+)[\s:-]*(.+?)(?:\s*\(.*\))?$', line, re.IGNORECASE)
        if not phase_match:
            phase_match = re.match(r'^##?\s*(\d+)[\s:\.]*(.+?)\s*Phase', line, re.IGNORECASE)
        if phase_match:
            phase_number = phase_match.group(1)
            phase_name = phase_match.group(2).strip()
            current_phase = {
                "phase_number": phase_number,
                "phase_name": phase_name,
                "tasks": []
            }
            result["phases"].append(current_phase)
            in_task_section = False
            continue
            
        # Check if it's a task header - try multiple patterns
        task_match = re.match(r'^###?\s*Task\s*(\d+\.\d+)[\s:-]*(.+?)(?:\s*\(.*\))?$', line, re.IGNORECASE)
        if not task_match:
            task_match = re.match(r'^###?\s*(\d+\.\d+)[\s:-]*(.+?)$', line, re.IGNORECASE)
        
        if task_match and current_phase is not None:
            task_id = task_match.group(1)
            task_name = task_match.group(2).strip()
            
            current_task = {
                "task_id": task_id,
                "task_name": task_name,
                "assigned_to": [],  # Initialize as list for multiple assignees
                "duration": "",
                "resources": [],
                "dependencies": []
            }
            current_phase["tasks"].append(current_task)
            in_task_section = True
            continue
        
        # Check for task details in various formats
        if current_task and in_task_section:
            # Format 1: - **Label:** Value
            label_match = re.match(r'[-*•]?\s*\*\*(.*?)[:]\*\*(.*)', line)
            if not label_match:
                # Format 2: **Label:** Value
                label_match = re.match(r'\*\*(.*?)[:]\*\*(.*)', line)
            if not label_match:
                # Format 3: - Label: Value
                label_match = re.match(r'[-*•]?\s*(.*?)[:](.*)', line)
            
            if label_match:
                detail_type = label_match.group(1).lower().strip()
                detail_value = label_match.group(2).strip()
                
                # Handle "Assigned to" field (check multiple possible phrasings)
                if any(term in detail_type for term in ["assigned to", "assignee", "responsible", "team member"]):
                    # Extract assignees with roles
                    if not detail_value or detail_value.lower() in ["none", "n/a", "to be determined", "tbd"]:
                        current_task["assigned_to"] = ["Unassigned"]
                    else:
                        # Split by comma to handle multiple assignees
                        assignees = []
                        for part in detail_value.split(','):
                            part = part.strip()
                            if part:  # Only add non-empty parts
                                assignees.append(part)
                        current_task["assigned_to"] = assignees if assignees else ["Unassigned"]
                
                # Handle "Duration" field (check multiple possible phrasings)
                elif any(term in detail_type for term in ["duration", "time", "timeframe", "timeline", "period", "estimated time"]):
                    if not detail_value or detail_value.lower() in ["none", "n/a", "to be determined", "tbd"]:
                        current_task["duration"] = "To Be Determined"
                    else:
                        current_task["duration"] = detail_value
                
                # Handle "Resources needed" field
                elif any(term in detail_type for term in ["resource", "tools", "materials", "equipment"]):
                    if not detail_value or detail_value.lower() in ["none", "n/a", "to be determined", "tbd"]:
                        current_task["resources"] = []
                    else:
                        resources = []
                        for part in detail_value.split(','):
                            part = part.strip()
                            if part:  # Only add non-empty parts
                                resources.append(part)
                        current_task["resources"] = resources
            
            # Special case: line might directly mention assigned people or duration without formal label
            elif "assigned to" in line.lower() and ":" in line:
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    assignees = []
                    for part in parts[1].split(','):
                        part = part.strip()
                        if part:  # Only add non-empty parts
                            assignees.append(part)
                    current_task["assigned_to"] = assignees if assignees else ["Unassigned"]
            elif "duration" in line.lower() and ":" in line:
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    current_task["duration"] = parts[1].strip()
    
    # Post-processing: Ensure every task has valid assigned_to and duration
    for phase in result["phases"]:
        for task in phase["tasks"]:
            # Convert assigned_to list to comma-separated string if it's a list
            if isinstance(task["assigned_to"], list):
                if not task["assigned_to"]:
                    task["assigned_to"] = "Unassigned"
                else:
                    task["assigned_to"] = ", ".join(task["assigned_to"])
            elif not task["assigned_to"]:
                task["assigned_to"] = "Unassigned"
                
            # Set default duration if empty
            if not task["duration"]:
                task["duration"] = "To Be Determined"
    
    # Debug: Log the result to help troubleshoot
    print(f"Parsed {len(result['phases'])} phases with a total of {sum(len(phase['tasks']) for phase in result['phases'])} tasks")
    
    # For debugging: Print out some sample assigned_to values
    if result['phases'] and result['phases'][0]['tasks']:
        print(f"Sample assigned_to from first task: {result['phases'][0]['tasks'][0]['assigned_to']}")
        print(f"Sample duration from first task: {result['phases'][0]['tasks'][0]['duration']}")
    
    return result