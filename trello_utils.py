import os
import requests

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_OAUTH_TOKEN = os.getenv("TRELLO_OAUTH_TOKEN")

def create_board(board_name):
    """Creates a Trello board with the given name."""
    url = "https://api.trello.com/1/boards/"
    query = {
        "name": board_name,
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.post(url, params=query)
    return response.json()

def get_board_id(board_name):
    """Fetches the ID of a Trello board based on its name."""
    url = f"https://api.trello.com/1/members/me/boards"
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

def create_list(board_id, list_name):
    """Creates a new list on a specified Trello board."""
    url = "https://api.trello.com/1/lists"
    query = {
        "name": list_name,
        "idBoard": board_id,
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.post(url, params=query)
    return response.json()

def get_list_id(board_id, list_name):
    """Gets the ID of a list from a given board."""
    url = f"https://api.trello.com/1/boards/{board_id}/lists"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.get(url, params=query)
    lists = response.json()
    for lst in lists:
        if lst["name"] == list_name:
            return lst["id"]
    return None

def create_card(list_id, card_name, description=""):
    """Creates a new card inside a Trello list."""
    url = "https://api.trello.com/1/cards"
    query = {
        "name": card_name,
        "desc": description,
        "idList": list_id,
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.post(url, params=query)
    return response.json()

def update_card_status(card_id, new_status):
    """Updates the status of a card by moving it to a new list."""
    url = f"https://api.trello.com/1/cards/{card_id}"
    query = {
        "idList": new_status,
        "key": TRELLO_API_KEY,
        "token": TRELLO_OAUTH_TOKEN
    }
    response = requests.put(url, params=query)
    return response.json()
