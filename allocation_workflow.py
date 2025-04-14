import os
import json
from parse_allocation import parse_allocation_plan
from trello_utils import save_tasks_to_json, check_and_add_tasks

def parse_and_save_allocation(markdown_file="allocation_plan.md", json_file="allocation_tasks.json"):
    """Parse the allocation plan from markdown and save it in the format expected by trello_utils."""
    
    if not os.path.exists(markdown_file):
        print(f"❌ Error: Allocation plan file '{markdown_file}' not found.")
        return False
    
    with open(markdown_file, "r") as f:
        allocation_text = f.read()
    
    tasks = parse_allocation_plan(allocation_text)
    
    if not tasks:
        print("❌ Error: No tasks were parsed from the allocation plan.")
        return False
    
    print(f"✅ Successfully parsed {len(tasks)} tasks from the allocation plan.")
    

    save_tasks_to_json(tasks)
    
    return True

if __name__ == "__main__":
    if parse_and_save_allocation():
        print("🚀 Starting Trello task management process...")
        check_and_add_tasks()
    else:
        print("❌ Failed to process allocation plan.")