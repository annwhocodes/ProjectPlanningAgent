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


def create_card(list_id, task_name, description):
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
    print(f"🔹 Trello API Response Text: {response.text}")
    if response.status_code != 200:
        print(f"❌ Trello API Error: {response.status_code} - {response.text}")
        return None
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Trello API returned an empty or invalid response.")
        return None


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
    phase_1_tasks = []
    phase_2_tasks = []

    for task in tasks:
        phase_str = task.get("phase", "")
        # Extract just the number at the beginning
        if phase_str.startswith("1"):
            phase_1_tasks.append(task)
        elif phase_str.startswith("2"):
            phase_2_tasks.append(task)
    
    return phase_1_tasks, phase_2_tasks


def add_tasks_from_allocation(board_id, tasks, phase_list_name):
    phase_list_id = get_or_create_list(board_id, phase_list_name)

    for task in tasks:
        task_name = task.get("task_name")
        description = task.get("description", "Task Description")
        print(f"📌 Adding Task to Trello: {task_name}")
        create_card(phase_list_id, task_name, description)
    
    print(f"✅ Tasks from {phase_list_name} added to Trello successfully!")


def check_phase_1_completion(board_id, phase_1_list_name):
    phase_1_list_id = get_or_create_list(board_id, phase_1_list_name)

    url = f"{BASE_URL}/lists/{phase_1_list_id}/cards"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    print(f"🔍 Checking completion status for list: {phase_1_list_name} (ID: {phase_1_list_id})")
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
    
 
    phase_1_tasks, phase_2_tasks = parse_allocation_tasks(tasks)
    
    
    add_tasks_from_allocation(board_id, phase_1_tasks, "Phase 1 - Not Started")
    
    
    while True:
        print("🔄 Checking if all Phase 1 tasks are completed...")
        if check_phase_1_completion(board_id, "Phase 1 - Not Started"):
            print("✅ Phase 1 tasks completed. Proceeding to add Phase 2 tasks.")
            add_tasks_from_allocation(board_id, phase_2_tasks, "Phase 2 - Not Started")
            break  
        
        print("⚠️ Phase 1 tasks are not completed yet.")
        time.sleep(120)  

if __name__ == "__main__":
    check_and_add_tasks()