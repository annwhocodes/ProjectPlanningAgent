import os
import requests
import json
from dotenv import load_dotenv

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
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN,
        "idList": list_id,
        "name": task_name,
        "desc": description
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
