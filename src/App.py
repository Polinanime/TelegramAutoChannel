from typing import Dict
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
DATA_PATH = os.path.join(current_dir, 'data/referenceChannels.json')
STATS_PATH = os.path.join(current_dir, 'tmp/stats.json')
CHECK_NUMBER = -1
CHANNELS_NUMBER = 0
CHECK_FREQ = 30
CHANNEL_ID = 0

def load_app(api: Dict[str,str|None]) -> Client:
    global CHANNEL_ID
    
    # CREATE APP
    if (None in api.values() or api["api_id"] is None or api["api_hash"] is None):
        raise ValueError("API dictionary is none")
    app = Client("ChannelBuilder", api_id=api["api_id"], api_hash=api["api_hash"])
    app.add_handler(MessageHandler(handle_channel_message, filters.channel))
    
    CHANNEL_ID = api['channel_id']
    
    return app

def handle_channel_message(client: Client, message: Message) -> None:
        
    chat: Chat = message.sender_chat
    channel_name = chat.username
    
    print(channel_name)
    
    if not is_whitelisted(channel_name):
        return
    
    last_post = get_stats(channel_name)
    
    if last_post == -1:
        # Ok its the first post so repost
        do_post = True
    else:
        do_post = to_post_or_not_to_post(last_post, get_channels_number())
    
    if do_post:
        print('POSTED')
        repost(client, message)
    else:
        print('NOT POSTED')
        
    load_stats(channel_name)
    
    return

def repost(client: Client, message: Message) -> None:
    
    client.forward_messages(
        CHANNEL_ID,
        from_chat_id=message.chat.id,
        message_ids=message.id
    )
    
    return 
    

def is_whitelisted(username:str) -> bool:
    with open(DATA_PATH, 'r') as file:
        data = json.load(file)
    return username in data and data[username]

def get_stats(username: str) -> int:
    with open(STATS_PATH, 'r') as file:
        data = json.load(file)
    return data[username] if username in data else -1 # -1 if there were not posts yet

def load_stats(username: str) -> None:
    with open(STATS_PATH, 'r') as file:
        data = json.load(file)
    data[username] = int(datetime.timestamp(datetime.now()))
    
    with open(STATS_PATH, 'w') as file:
        json.dump(data, file, indent=2)
    
    return


def get_channels_number():
    global CHECK_FREQ, CHECK_NUMBER, CHANNELS_NUMBER
    if CHECK_NUMBER == CHECK_FREQ or CHECK_NUMBER == -1:
        CHECK_NUMBER = 0
        with open(DATA_PATH, 'r') as file:
            data = json.load(file)
        CHANNELS_NUMBER = list(data.values()).count(True)
    return CHANNELS_NUMBER


def to_post_or_not_to_post(last_post: int, channels_number: int, multiplier = 1000) -> bool:
    time_now = int(datetime.timestamp(datetime.now()))
    
    if time_now == last_post:
        return False
    
    chance = 1.0 - multiplier * channels_number / (time_now - last_post)
    print(chance)
    print(f'Chan num: {channels_number}, time now: {time_now}, last_post: {last_post}')
    if chance <= 0:
        return False
    return random() < chance

