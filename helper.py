import os
import json

BALANCE_FILE = 'balances.json'
BET_FILE = 'bets.json'
CHANNEL_FILE = 'channels.json'

########################################
# BALANCE HELPER COMMANDS
########################################
# Loads the balances from the JSON file
def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Saves the balances to the JSON file
def save_balances(user_balances):
    with open(BALANCE_FILE, 'w') as f:
        json.dump(user_balances, f, indent=4)

# Initializes all new user's balances
def init_user_balance(user_id, user_balances):
    if user_id not in user_balances:
        user_balances[user_id] = 0
    return user_balances

# Gets the balance for a specific user
def get_user_balance(user_id, user_balances):
    return user_balances.get(user_id, 0)

# Modifies the balance for a specific user
def modify_user_balance(user_id, amount, user_balances):
    user_balances[user_id] = user_balances.get(user_id, 0) + amount

    if user_balances[user_id] < 0:
        return False
    
    save_balances(user_balances)
    return True

########################################
# BET HELPER COMMANDS
########################################

def load_bets():
    if os.path.exists(BET_FILE):
        with open(BET_FILE, 'r') as f:
            bets_data = json.load(f)
            return bets_data.get("user_bets", {}), bets_data.get("all_bets", {})
    return {}, {}

def save_bets(user_bets, all_bets):
    data = {
        "user_bets": user_bets,
        "all_bets": all_bets
    }
    with open(BET_FILE, 'w') as f:
        json.dump(data, f, indent=4)

########################################
# CHANNEL HELPER COMMANDS
########################################

def load_channel_ids():
    if os.path.exists(CHANNEL_FILE):
        with open(CHANNEL_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_channel_ids(guild_id, channel_id):
    channel_data = load_channel_ids()
    channel_data[guild_id] = channel_id

    with open(CHANNEL_FILE, 'w') as f:
        json.dump(channel_data, f, indent=4)
