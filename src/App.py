from typing import Dict, List
import asyncio
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message, Chat
from pyrogram import enums
from datetime import datetime
from random import random
import time
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
POSTED = {}
COUNTER = 0

def load_app(api: Dict[str,str|None]) -> Client:
    global CHANNEL_ID
    
    # CREATE APP
    if (None in api.values() or api["api_id"] is None or api["api_hash"] is None):
        raise ValueError("API dictionary is none")

    app = Client("ChannelBuilder", api_id=api["api_id"], api_hash=api["api_hash"])
    app.add_handler(MessageHandler(handle_channel_message, filters.channel))
    app.add_handler(MessageHandler(handle_command, filters.AndFilter(filters.chat("self"), filters.command(["add", "vip", "mult", "remove", "unvip", "ping"], prefixes="%%"))))
    
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
    
    if cmd[0] == "ping":
        client.send_message(message.chat.id, "Pong")
        return
    
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
    channel_name: str = chat.username
    channel_id: str = str(chat.id)
    
    load_settings() # Why so many times? Every single post....

    print(message.chat.id)
    
    do_post = to_post_or_not_to_post(channel_name, get_channels_number(), channel_id, multiplier=0)
    
    repost(client, message, do_post)
    print(("POSTED" if do_post else "NOT POSTED") + f" {channel_name} {channel_id}") 
        
    return

def repost(client: Client, message: Message, do_post: bool) -> None:
    print(time.time())
    print(message.chat.id)
    print(message.id)
    print(CHANNEL_ID)
       
    if not do_post:
        return
    
    if message.media_group_id:
        media_group = client.get_media_group(message.chat.id, message.id)
        has_caption = any([True for msg in media_group if msg.caption is not None])
    else:
        has_caption = False
    
    new_caption = generate_caption(message)
    
    try:
        if POSTED.get(message.chat.id) == message.media_group_id and message.media_group_id is not None:
            print("ALREADY POSTED")
            return
        
        client.copy_media_group(CHANNEL_ID, message.chat.id, message_id=message.id, captions=new_caption)
        print("GROUP")
        POSTED[message.chat.id] = message.media_group_id

    except Exception as e:
        print("ERROR: ", e)
        if message.photo and e is not TypeError:
            if not (not message.media_group_id or (message.media_group_id and not has_caption)):
                return
            print("PHOTO")
            client.send_photo(CHANNEL_ID, message.photo.file_id, caption=new_caption)
            POSTED[message.chat.id] = message.media_group_id
        elif message.video and e is not TypeError:
            if not (not message.media_group_id or (message.media_group_id and not has_caption)):
                return
            print("VIDEO")
            client.send_video(CHANNEL_ID, message.video.file_id, caption=new_caption)
            POSTED[message.chat.id] = message.media_group_id
        elif message.text is not None:
            print("TEXT")
            print(CHANNEL_ID)
            client.send_message(CHANNEL_ID, new_caption, disable_web_page_preview=True)
        else:
            print("FORWARD")
            # print("text:", message.text)
            # print("caption:", message.caption)
            # print("raw: ", message.raw)
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
def to_post_or_not_to_post(channel_name: str, channels_number: int, channel_id: str, multiplier = 1000) -> bool:
    if not is_whitelisted(channel_name) and not is_whitelisted(channel_id):    # Do not post garbage channels
        return False

    if is_channel_vip(channel_name):    # We always post +ANTURAJ
        return True
    
    last_post = get_stats(channel_name)
    if last_post == -1: # The first post for this channel in history -> always post
        return True
    
    time_now = int(datetime.timestamp(datetime.now()))
    
    if time_now == last_post:   # Too fast posting 
        return False
    
    chance = 1.0 - multiplier * channels_number / (time_now - last_post)    # formula can be changed in future
    print(chance)
    print(f"Channel num: {channels_number}, time now: {time_now}, last_post: {last_post}") # Some logs. TODO: normal logging system
    if chance <= 0:
        return False
    return random() < chance


def generate_hashtag(chat: Chat) -> str:
    name: str = chat.title if chat.title else chat.first_name
    name = name.replace(" ", "_")
    hashtag: str = "#"
    for i in range(len(name)):
        if name[i].isdigit() or name[i].isalpha() or name[i] == "_":
            hashtag += name[i]
    return hashtag


def generate_caption(message: Message) -> str:
    caption: str = ""
    if message.caption:
        caption = message.caption.html
    elif message.text:
        caption = message.text.html
        
    real_id: str = str(message.chat.id)[4:] if str(message.chat.id).startswith("-100") else message.chat.id
    hashtag: str = generate_hashtag(message.chat)
    
    if message.forward_from_chat and message.forward_from_chat.username:
        caption += f"\n\nПереслано из: [{message.forward_from_chat.title}](https://t.me/c/{real_id}/{message.id})"
            
    caption += f"\n\nАвтор: [{message.chat.title}](https://t.me/c/{real_id}/{message.id})"
    caption += f" ({hashtag})"
    caption += "\n\n[Стена Иннополис. Подписаться.](https://t.me/+GC10Uk2uhnsyN2Y6)"
    return caption
        