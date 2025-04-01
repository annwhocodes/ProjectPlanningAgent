import os
import requests
import json
import time
from dotenv import load_dotenv
import datetime

load_dotenv()

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_OAUTH_TOKEN = os.getenv("TRELLO_OAUTH_TOKEN")
BOARD_NAME = "My Project Manager Crew"
JSON_FILE = "allocation_tasks.json"

BASE_URL = "https://api.trello.com/1"


def create_board(board_name):
    url = f"{BASE_URL}/boards/"
    query = {
        "name": board_name,
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.post(url, params=query)
    return response.json()


def get_board_id(board_name=BOARD_NAME):
    url = f"{BASE_URL}/members/me/boards"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.get(url, params=query)
    boards = response.json()
    for board in boards:
        if board["name"] == board_name:
            return board["id"]
    return None


def get_or_create_list(board_id, list_name):
    url = f"{BASE_URL}/boards/{board_id}/lists"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        lists = response.json()
        for lst in lists:
            if lst["name"] == list_name:
                return lst["id"]
    create_url = f"{BASE_URL}/lists"
    create_params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "name": list_name,
        "idBoard": board_id
    }
    response = requests.post(create_url, params=create_params)
    return response.json().get("id")


def get_member_id_by_username(username):
    """Get Trello member ID by username."""
    url = f"{BASE_URL}/members/{username}"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"⚠️ Member with username '{username}' not found")
    return None


def get_board_members(board_id):
    """Get all members of a board with their IDs."""
    url = f"{BASE_URL}/boards/{board_id}/members"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        return {member.get("username"): member.get("id") for member in response.json()}
    return {}


def create_card(list_id, task_name, description, assigned_to=None):
    url = f"{BASE_URL}/cards"
    due_date = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
    
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "idList": list_id,
        "name": task_name,
        "desc": description,
        "due": due_date
    }
    
    response = requests.post(url, params=params)
    print(f"🔹 Trello API Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Trello API Error: {response.status_code} - {response.text}")
        return None
    
    try:
        card = response.json()
        
        # Assign the card to a member if provided
        if assigned_to and card.get("id"):
            assign_member_to_card(card.get("id"), assigned_to)
            
        return card
    except requests.exceptions.JSONDecodeError:
        print("❌ Trello API returned an empty or invalid response.")
        return None


def assign_member_to_card(card_id, member_id):
    """Assign a member to a card."""
    url = f"{BASE_URL}/cards/{card_id}/idMembers"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "value": member_id
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print(f"✅ Assigned member to card {card_id}")
        return True
    print(f"❌ Failed to assign member to card: {response.status_code} - {response.text}")
    return False


def update_card_status(card_id, new_list_id):
    url = f"{BASE_URL}/cards/{card_id}"
    query = {
        "idList": new_list_id,
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.put(url, params=query)
    return response.json()


def save_tasks_to_json(task_list):
    try:
        with open(JSON_FILE, "w") as f:
            json.dump({"tasks": task_list}, f, indent=4)
        print(f"✅ Tasks saved to {JSON_FILE}")
    except Exception as e:
        print(f"❌ Error saving allocation to JSON: {str(e)}")


def load_tasks_from_json():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f).get("tasks", [])
    print("⚠️ No tasks found in JSON file.")
    return []


def parse_allocation_tasks(tasks):
    """Parse tasks into different phases based on phase number."""
    phases = {}
    
    for task in tasks:
        phase_str = task.get("phase", "")
        # Extract phase number
        phase_num = ""
        for char in phase_str:
            if char.isdigit():
                phase_num += char
            else:
                break
                
        if phase_num:
            if phase_num not in phases:
                phases[phase_num] = []
            phases[phase_num].append(task)
    
    return phases


def add_tasks_from_allocation(board_id, tasks, phase_list_name):
    phase_list_id = get_or_create_list(board_id, phase_list_name)
    board_members = get_board_members(board_id)
    
    for task in tasks:
        task_name = task.get("task_name")
        description = task.get("description", "Task Description")
        assignee = task.get("assigned_to")
        
        print(f"📌 Adding Task to Trello: {task_name}")
        
        member_id = None
        if assignee:
            # Try to find member ID from board members
            member_id = board_members.get(assignee)
            
            # If not found on board, try to get by username
            if not member_id:
                member_id = get_member_id_by_username(assignee)
                
            if member_id:
                print(f"👤 Assigning task to: {assignee}")
            else:
                print(f"⚠️ Could not find member: {assignee}")
        
        create_card(phase_list_id, task_name, description, member_id)
    
    print(f"✅ Tasks from {phase_list_name} added to Trello successfully!")


def check_phase_completion(board_id, phase_list_name):
    phase_list_id = get_or_create_list(board_id, phase_list_name)

    url = f"{BASE_URL}/lists/{phase_list_id}/cards"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    print(f"🔍 Checking completion status for list: {phase_list_name} (ID: {phase_list_id})")
    response = requests.get(url, params=query)
    
    if response.status_code == 200:
        cards = response.json()
        print(f"📊 Found {len(cards)} cards in the list")
        
        if not cards:  
            print("✅ No cards in list, considering phase complete")
            return True
            
        completed_cards = [card for card in cards if card.get("dueComplete", False) == True]
        print(f"✅ {len(completed_cards)}/{len(cards)} cards are completed")
        
        is_complete = len(completed_cards) == len(cards)
        
        if is_complete:
            print("🎉 All cards are completed!")
        else:
            print("⏳ Some cards are still pending completion")
            
        return is_complete
    else:
        print(f"❌ Error getting cards: {response.status_code} - {response.text}")
        return False


def check_and_add_tasks():
    board_id = get_board_id()
    
    # Load tasks from JSON
    tasks = load_tasks_from_json()
    
    # Parse tasks into multiple phases
    phases = parse_allocation_tasks(tasks)
    
    # Sort phases by number to ensure sequential processing
    sorted_phases = sorted(phases.keys(), key=int)
    
    current_phase_index = 0
    
    while current_phase_index < len(sorted_phases):
        current_phase = sorted_phases[current_phase_index]
        current_phase_name = f"Phase {current_phase} - Not Started"
        next_phase_name = f"Phase {current_phase} - Completed"
        
        print(f"🔄 Working on {current_phase_name}")
        
        # Add tasks for the current phase if they don't exist yet
        add_tasks_from_allocation(board_id, phases[current_phase], current_phase_name)
        
        # Keep checking until current phase is complete
        while True:
            print(f"🔄 Checking if all tasks in {current_phase_name} are completed...")
            if check_phase_completion(board_id, current_phase_name):
                print(f"✅ Tasks in {current_phase_name} completed.")
                
                # Move completed tasks to the completed list
                completed_list_id = get_or_create_list(board_id, next_phase_name)
                
                # Move to next phase
                current_phase_index += 1
                
                if current_phase_index < len(sorted_phases):
                    next_phase = sorted_phases[current_phase_index]
                    print(f"➡️ Moving to Phase {next_phase}")
                else:
                    print("🎉 All phases completed!")
                
                break
            
            print(f"⚠️ Tasks in {current_phase_name} are not completed yet.")
            time.sleep(120)  # Check every 2 minutes

if __name__ == "__main__":
    check_and_add_tasks()