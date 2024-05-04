from typing import Dict
import asyncio
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message, Chat

class channel_builder:
    app: Client
    def __init__(self, api: Dict[str,str|None]) -> None:
        # CREATE APP
        if (None in api.values() or api["api_id"] is None or api["api_hash"] is None):
            raise ValueError("API dictionary is none")
        self.app = Client("ChannelBuilder", api_id=api["api_id"], api_hash=api["api_hash"])
        
        #DEFINE ALL HANDLERS
        self.app.add_handler(MessageHandler(self.handle_channel_message, filters.channel))
        
        return
    
    def handle_channel_message(self, client: Client, message: Message):
        
        author: Chat = message.sender_chat
        
        return
    
    def run(self) -> None:
        self.app.run()