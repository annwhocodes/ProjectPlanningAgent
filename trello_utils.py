import os
import requests
import json
import time
from dotenv import load_dotenv
import datetime
import re

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


def search_trello_members(query):
    """Search for Trello members by name or username."""
    url = f"{BASE_URL}/search/members"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "query": query,
        "limit": 5  
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"⚠️ Failed to search for members: {response.status_code} - {response.text}")
    return []


def get_member_id_by_username(username):
    """Get Trello member ID by username."""
    if "john doe" in username.lower() or "johndoe" in username.lower():
        members = search_trello_members("John Doe")
        if members:
            for member in members:
                if "john" in member.get("username", "").lower() or "john" in member.get("fullName", "").lower():
                    print(f"✅ Found John Doe: {member.get('fullName')} ({member.get('username')})")
                    return member.get("id")  
        
        print("⚠️ Using fallback for John Doe")
        return "johndoe892004"  
    
    # Special case for Bob Smith
    elif "bob smith" in username.lower() or "bobsmith" in username.lower():
        url = f"{BASE_URL}/members/bobsmith892004"
        query = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_OAUTH_TOKEN
        }
        response = requests.get(url, params=query)
        if response.status_code == 200:
            print(f"✅ Found Bob Smith via direct lookup")
            return response.json().get("id")
        
        members = search_trello_members("Bob Smith")
        if members:
            for member in members:
                if "bob" in member.get("username", "").lower() or "bob" in member.get("fullName", "").lower():
                    print(f"✅ Found Bob Smith: {member.get('fullName')} ({member.get('username')})")
                    return member.get("id")
        
        print("⚠️ Using fallback for Bob Smith")
        return "bobsmith892004"
    
    # Special case
    elif "piyush lavaniya" in username.lower() or "piyushlavaniya" in username.lower():
        # First try direct lookup with the known username
        url = f"{BASE_URL}/members/piyushlavaniya"
        query = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_OAUTH_TOKEN
        }
        response = requests.get(url, params=query)
        if response.status_code == 200:
            print(f"✅ Found Piyush Lavaniya via direct lookup")
            return response.json().get("id")
            
        # If direct lookup fails, try searching
        members = search_trello_members("Piyush Lavaniya")
        if members:
            for member in members:
                if "piyush" in member.get("username", "").lower() or "piyush" in member.get("fullName", "").lower():
                    print(f"✅ Found Piyush Lavaniya: {member.get('fullName')} ({member.get('username')})")
                    return member.get("id")
        
        print("⚠️ Using fallback for Piyush Lavaniya")
        return "piyushlavaniya"
        
    url = f"{BASE_URL}/members/{username}"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        return response.json().get("id")
    
    members = search_trello_members(username)
    if members:
        for member in members:
            if member.get("username") and (
                username.lower() in member.get("username").lower() or
                username.lower() in member.get("fullName", "").lower()
            ):
                print(f"✅ Found member via search: {member.get('fullName')} ({member.get('username')})")
                return member.get("id")
    
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
        members = {member.get("username"): member.get("id") for member in response.json()}
        print(f"📊 Board members: {members}")
        return members
    return {}


def create_card(list_id, task_name, description, assigned_to=None):
    url = f"{BASE_URL}/cards"
    due_date = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
    
    detailed_description = description
    if assigned_to:
        detailed_description += f"\n\nAssigned to: {assigned_to}"
    
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "idList": list_id,
        "name": task_name,
        "desc": detailed_description,
        "due": due_date
    }

    response = requests.post(url, params=params)
    print(f"🔹 Trello API Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Trello API Error: {response.status_code} - {response.text}")
        return None
    
    try:
        card = response.json()
        
        if assigned_to and card.get("id"):
            print(f"👤 Attempting to assign card to: {assigned_to}")
            
            board_id = get_board_id()
            
            board_members = get_board_members(board_id)
            member_id = None
            
            if "john doe" in assigned_to.lower() or "johndoe" in assigned_to.lower():
                print("🔍 Detected John Doe assignment")
                for username, user_id in board_members.items():
                    if "john" in username.lower():
                        member_id = user_id
                        print(f"✅ Found John Doe in board members: {username}")
                        break

                if not member_id:
                    member_id = get_member_id_by_username("John Doe")
                    if member_id:
                        add_member_to_board(board_id, member_id)
            elif "bob smith" in assigned_to.lower() or "bobsmith" in assigned_to.lower():
                print("🔍 Detected Bob Smith assignment")

                for username, user_id in board_members.items():
                    if "bob" in username.lower():
                        member_id = user_id
                        print(f"✅ Found Bob Smith in board members: {username}")
                        break

                if not member_id:
                    member_id = get_member_id_by_username("Bob Smith")
                    if member_id:
                        add_member_to_board(board_id, member_id)
            elif "piyush lavaniya" in assigned_to.lower() or "piyushlavaniya" in assigned_to.lower():
                print("🔍 Detected Piyush Lavaniya assignment")
                for username, user_id in board_members.items():
                    if "piyush" in username.lower():
                        member_id = user_id
                        print(f"✅ Found Piyush Lavaniya in board members: {username}")
                        break
                
                if not member_id:
                    member_id = get_member_id_by_username("Piyush Lavaniya")
                    if member_id:
                        add_member_to_board(board_id, member_id)
            else:
                for username, user_id in board_members.items():
                    if assigned_to.lower() in username.lower() or assigned_to.lower() in user_id.lower():
                        member_id = user_id
                        print(f"✅ Found board member match: {username}")
                        break
                

                if not member_id:
                    member_id = get_member_id_by_username(assigned_to)
                    if member_id:
                    
                        add_member_to_board(board_id, member_id)

            if member_id:
                success = assign_member_to_card(card.get("id"), member_id)
                if not success:
                    print(f"⚠️ Failed to assign {assigned_to} to card, trying alternative approach")

            else:
                print(f"⚠️ No member ID found for '{assigned_to}'")
        
        return card
    except requests.exceptions.JSONDecodeError:
        print("❌ Trello API returned an empty or invalid response.")
        return None
    
def add_member_to_board(board_id, member_id):
    """Add a member to board by member ID."""
    board_url = f"{BASE_URL}/boards/{board_id}/members"
    board_params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "idMember": member_id,
        "type": "normal"
    }
    
    board_response = requests.put(board_url, params=board_params)
    status = board_response.status_code
    print(f"📝 Adding member to board result: {status}")
    
    if status == 200:
        print(f"✅ Successfully added member to board")
        return True
    elif status == 401 or status == 403:
        print("⚠️ Authentication issue or insufficient permissions to add members")
    elif status == 409:
        print("ℹ️ Member is already on the board")
        return True
    else:
        print(f"⚠️ Failed to add member to board: {board_response.text}")
    
    return status == 200 or status == 409


def add_member_to_board_and_card(board_id, card_id, username):
    """Add a member to board if not already a member, then assign to card."""
    member_id = get_member_id_by_username(username)
    
    if member_id:
        added_to_board = add_member_to_board(board_id, member_id)
        
        if added_to_board:
            return assign_member_to_card(card_id, member_id)
        else:
            print(f"⚠️ Could not add member to board, skipping card assignment")
            return False
    else:
        print(f"❌ Could not find member ID for username: {username}")
        return False


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
    else:
        put_response = requests.put(url, params=params)
        if put_response.status_code == 200:
            print(f"✅ Assigned member to card using PUT {card_id}")
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
            try:
                data = json.load(f)
                print(f"📚 Loaded task data from JSON: {JSON_FILE}")
                tasks = data.get("tasks", [])
                if tasks and len(tasks) > 0:
                    print(f"📝 First task sample: {tasks[0]}")
                
                if "tasks" in data:
                    return data.get("tasks", [])
                else:
                    all_tasks = []
                    for phase in data.get("phases", []):
                        all_tasks.extend(phase.get("tasks", []))
                    return all_tasks
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding JSON: {str(e)}")
                return []
    print("⚠️ No tasks found in JSON file.")
    return []


def parse_allocation_tasks(tasks):
    """Parse tasks into different phases based on phase number."""
    phases = {}
    
    print(f"Parsing {len(tasks)} tasks into phases...")
    
    for task in tasks:
        phase_str = task.get("phase", "")
        phase_match = re.match(r'(\d+)\.?.*', phase_str)
        
        if phase_match:
            phase_num = phase_match.group(1)
            if phase_num not in phases:
                phases[phase_num] = []
            phases[phase_num].append(task)
        else:
            if "0" not in phases:
                phases["0"] = []
            phases["0"].append(task)
    
    # Debug output
    for phase_num, phase_tasks in phases.items():
        print(f"Phase {phase_num}: {len(phase_tasks)} tasks")
    
    return phases


def add_tasks_from_allocation(board_id, tasks, phase_list_name):
    phase_list_id = get_or_create_list(board_id, phase_list_name)
    board_members = get_board_members(board_id)
    
    for task in tasks:
        task_name = task.get("task_name")
        description = f"Task: {task_name}\n"
        if task.get("duration"):
            description += f"Duration: {task.get('duration')}\n"
        if task.get("resources") and len(task.get("resources")) > 0:
            description += f"Resources: {', '.join(task.get('resources'))}\n"
        
        assignee = task.get("assigned_to")
        
        print(f"📌 Adding Task to Trello: {task_name}")
        print(f"👤 Assigned to: {assignee}")
        
        create_card(phase_list_id, task_name, description, assignee)
    
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
    
    tasks = load_tasks_from_json()
    

    phases = parse_allocation_tasks(tasks)

    sorted_phases = sorted(phases.keys(), key=int)
    
    current_phase_index = 0
    
    while current_phase_index < len(sorted_phases):
        current_phase = sorted_phases[current_phase_index]
        current_phase_name = f"Phase {current_phase} - Not Started"
        next_phase_name = f"Phase {current_phase} - Completed"
        
        print(f"🔄 Working on {current_phase_name}")
        
        add_tasks_from_allocation(board_id, phases[current_phase], current_phase_name)
        
        while True:
            print(f"🔄 Checking if all tasks in {current_phase_name} are completed...")
            if check_phase_completion(board_id, current_phase_name):
                print(f"✅ Tasks in {current_phase_name} completed.")
                
                completed_list_id = get_or_create_list(board_id, next_phase_name)
                

                current_phase_index += 1
                
                if current_phase_index < len(sorted_phases):
                    next_phase = sorted_phases[current_phase_index]
                    print(f"➡️ Moving to Phase {next_phase}")
                else:
                    print("🎉 All phases completed!")
                
                break
            
            print(f"⚠️ Tasks in {current_phase_name} are not completed yet.")
            time.sleep(120) 

if __name__ == "__main__":
    check_and_add_tasks()