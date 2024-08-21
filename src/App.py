from typing import Dict, List
import asyncio
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message, Chat
from pyrogram import idle
from datetime import datetime
from random import random
import json

import os

current_dir = os.getcwd()
DATA_PATH = os.path.join(current_dir, "data/referenceChannels.json")
VIP_PATH = os.path.join(current_dir, "data/priorityChannels.json")
STATS_PATH = os.path.join(current_dir, "tmp/stats.json")
SETTINGS_PATH = os.path.join(current_dir, "data/settings.json")
CHECK_NUMBER = -1
CHANNELS_NUMBER = 0
CHECK_FREQ = 30
CHANNEL_ID = 0
MULTIPLIER = 0

def load_app(api: Dict[str,str|None]) -> Client:
    global CHANNEL_ID
    
    # CREATE APP
    if (None in api.values() or api["api_id"] is None or api["api_hash"] is None):
        raise ValueError("API dictionary is none")

    app = Client("ChannelBuilder", api_id=api["api_id"], api_hash=api["api_hash"])
    app.add_handler(MessageHandler(handle_channel_message, filters.channel))
    app.add_handler(MessageHandler(handle_command, filters.AndFilter(filters.chat("self"), filters.command(["add", "vip", "mult", "remove", "unvip"], prefixes="%%"))))
    
    CHANNEL_ID = api["channel_id"]
    
    return app

# Func to handle commands:
#   * VIP - add to vip channels
#   * ADD - add new channel to follow
#   * MULT - change multiplier
#   * REMOVE - remove from followings
#   * UNVIP - remove from vips
def handle_command(client: Client, message: Message) -> None:
    print("COMMAND:" + message.text)
    cmd = message.command
    
    if cmd[0] == "mult":
        change_multiplier(int(cmd[1]))
        return
    
    path = ""
    new_data = False
    
    if cmd[0] in ["add", "remove"]:
        path = DATA_PATH
    elif cmd[0] in ["vip", "unvip"]:
        path = VIP_PATH
        
    if cmd[0] in ["add", "vip"]:
        new_data = True
    elif cmd[0] in ["remove", "unvip"]:
        new_data = False
        
    print(f"Name: {cmd[1:]}, new_data: {new_data}, path: {path}")
        
    change_channels_data(cmd[1:], path, new_data)
        
    return

def change_multiplier(new_value: int) -> None:
    MULTIPLIER = new_value
    with open(SETTINGS_PATH, "r") as file:
        data = json.load(file)
    data["multiplier"] = new_value
    with open(SETTINGS_PATH, "w") as file:
        json.dump(data, file, indent=2)
    
    return
    
def change_channels_data(channels: List[str], path: str, new_data: bool) -> None:
    with open(path, "r") as file:
        data = json.load(file)
        
    for channel in channels:
        data[channel] = new_data
        
    with open(path, "w") as file:
        json.dump(data, file, indent=2)
        
    return

def handle_channel_message(client: Client, message: Message) -> None:    
    chat: Chat = message.sender_chat
    channel_name = chat.username
    
    load_settings() # Why so many times? Every single post....

    print(message.chat.id)
    do_post = to_post_or_not_to_post(channel_name, get_channels_number(), multiplier=0)
    
    repost(client, message, do_post)
    print(("POSTED" if do_post else "NOT POSTED") + f" {channel_name}") 
        
    save_stats(channel_name)    # save statistics for this channel
    
    return

def repost(client: Client, message: Message, do_post: bool) -> None:
    if not do_post:
        return
    
    client.forward_messages(
        CHANNEL_ID,
        from_chat_id=message.chat.id,
        message_ids=message.id
    )
    
    return 
    

def is_whitelisted(username:str) -> bool:
    with open(DATA_PATH, "r") as file:
        data = json.load(file)
    return username in data and data[username]


def get_stats(username: str) -> int:
    with open(STATS_PATH, "r") as file:
        data = json.load(file)
    return data[username] if username in data else -1 # -1 if there were not posts yet


def save_stats(username: str) -> None:
    with open(STATS_PATH, "r") as file:
        data = json.load(file)
    data[username] = int(datetime.timestamp(datetime.now()))
    
    with open(STATS_PATH, "w") as file:
        json.dump(data, file, indent=2)
    
    return

# Return if channel is prioritized (VIP in other words)
def is_channel_vip(channel_name: str) -> bool:
    with open(VIP_PATH, "r") as file:
        data = json.load(file)
    return channel_name in data and data[channel_name]

# Get channels number (used for posting chance formula)
def get_channels_number():
    global CHECK_FREQ, CHECK_NUMBER, CHANNELS_NUMBER
    if CHECK_NUMBER == CHECK_FREQ or CHECK_NUMBER == -1:    # Check if we need to recalculate channels number
        CHECK_NUMBER = 0
        with open(DATA_PATH, "r") as file:
            data = json.load(file)
        CHANNELS_NUMBER = list(data.values()).count(True)
    return CHANNELS_NUMBER

# Load settings from settings.json (Why it is not in .env? Because we do change it)
def load_settings():
    global MULTIPLIER
    with open(SETTINGS_PATH, "r") as file:
        data = json.load(file)
    MULTIPLIER = data["multiplier"]
    

# Function to decide if we need to repost
# It checks:
#   * is channel whitelisted
#   * is channel vip
#   * compares with last post time
def to_post_or_not_to_post(channel_name: str, channels_number: int, multiplier = 1000) -> bool:
    if not is_whitelisted(channel_name):    # Do not post garbage channels
        return False

    if is_channel_vip(channel_name):    # We always post +ANTURAJ
        return True
    
    last_post = get_stats(channel_name)
    if last_post == -1: # The first post for this channel in history -> always post
        return True
    
    time_now = int(datetime.timestamp(datetime.now()))
    
    if time_now == last_post:   # To fast posting 
        return True
    
    chance = 1.0 - multiplier * channels_number / (time_now - last_post)    # formula can be changed in future
    print(chance)
    print(f"Channel num: {channels_number}, time now: {time_now}, last_post: {last_post}") # Some logs. TODO: normal logging system
    if chance <= 0:
        return False
    return random() < chance

