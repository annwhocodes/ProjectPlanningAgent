import re

def parse_allocation_plan(text):
    """Parse the allocation plan text into a structured format."""
    
    # Initialize the result structure
    result = {
        "phases": []
    }
    
    # Split the text into lines
    lines = text.strip().split('\n')
    
    current_phase = None
    current_task = None
    
    # Process each line
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if it's a phase header
        phase_match = re.match(r'^##\s+Phase\s+(\d+):\s+(.+)$', line)
        if phase_match:
            phase_number = phase_match.group(1)
            phase_name = phase_match.group(2)
            current_phase = {
                "phase_number": phase_number,
                "phase_name": phase_name,
                "tasks": []
            }
            result["phases"].append(current_phase)
            continue
        
        # Check if it's a task header
        task_match = re.match(r'^\*\s+Task\s+(\d+\.\d+):\s+(.+)$', line)
        if task_match and current_phase is not None:
            task_id = task_match.group(1)
            task_name = task_match.group(2)
            current_task = {
                "task_id": task_id,
                "task_name": task_name,
                "assigned_to": [],
                "duration": "",
                "resources": [],
                "dependencies": []
            }
            current_phase["tasks"].append(current_task)
            continue
        
        # Check for task details
        if current_task is not None:
            # Handle assigned to
            if line.startswith('* Assigned to:'):
                assigned_to = line.replace('* Assigned to:', '').strip()
                current_task["assigned_to"] = [name.strip() for name in assigned_to.split(',')]
            
            # Handle duration
            elif line.startswith('* Duration:'):
                duration = line.replace('* Duration:', '').strip()
                current_task["duration"] = duration
            
            # Handle resources
            elif line.startswith('* Resources:'):
                resources = line.replace('* Resources:', '').strip()
                if resources:
                    current_task["resources"] = [res.strip() for res in resources.split(',')]
            
            # Handle dependencies
            elif line.startswith('* Dependencies:'):
                dependencies = line.replace('* Dependencies:', '').strip()
                if dependencies:
                    current_task["dependencies"] = [dep.strip() for dep in dependencies.split(',')]
    
    return result