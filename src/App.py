import asyncio
import json
import logging
import os
from datetime import datetime
from random import random
from typing import Dict, List, Optional, Union
from time import sleep

from pyrogram import filters
from pyrogram.sync import idle
from pyrogram.client import Client
from pyrogram.errors import ImportFileInvalid
from pyrogram.types import Message, Chat
from pyrogram.handlers.message_handler import MessageHandler

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, api_data: Dict[str, Optional[str]]):
        self.current_dir = os.getcwd()
        self.data_path = os.path.join(self.current_dir, "data/referenceChannels.json")
        self.vip_path = os.path.join(self.current_dir, "data/priorityChannels.json")
        self.stats_path = os.path.join(self.current_dir, "tmp/stats.json")
        self.settings_path = os.path.join(self.current_dir, "data/settings.json")

        self.check_number = -1
        self.channels_number = 0
        self.check_freq = 30
        self.channel_id = api_data["channel_id"]
        self.multiplier = 0
        self.posted = {}
        self.posted_lock = asyncio.Lock()
        self.sleep_time = 1

        if None in api_data.values() or not api_data.get("api_id") or not api_data.get("api_hash"):
            raise ValueError("Invalid API credentials")

        self.client = Client(
            "ChannelBuilder",
            api_id=api_data["api_id"],
            api_hash=api_data["api_hash"]
        )

        self._setup_handlers()

    def _setup_handlers(self):
        """Setup message handlers for the bot"""
        self.client.add_handler(
            MessageHandler(self.handle_channel_message, filters.channel)
        )
        self.client.add_handler(
            MessageHandler(
                self.handle_command,
                filters.AndFilter(
                    filters.chat("self"),
                    filters.command(["add", "vip", "mult", "remove", "unvip", "ping"], prefixes="%%")
                )
            )
        )

    async def start(self):
        """Start the bot and keep it running"""
        await self.client.start()
        logger.info("Bot started successfully")
        await idle()

    def _load_json(self, path: str) -> Dict:
        """Load JSON data from file"""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            return {}

    def _save_json(self, path: str, data: Dict):
        """Save data to JSON file"""
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    async def handle_command(self, client: Client, message: Message):
        """Handle bot commands"""
        logger.info(f"Received command: {message.text}")
        cmd = message.command

        if not cmd:
            return

        if cmd[0] == "mult":
            await self.change_multiplier(int(cmd[1]))
            return

        if cmd[0] == "ping":
            await client.send_message(message.chat.id, "Pong")
            return

        path = self.data_path if cmd[0] in ["add", "remove"] else self.vip_path
        new_data = cmd[0] in ["add", "vip"]

        await self.change_channels_data(cmd[1:], path, new_data)

    async def change_multiplier(self, new_value: int):
        """Change multiplier value in settings"""
        self.multiplier = new_value
        data = self._load_json(self.settings_path)
        data["multiplier"] = new_value
        self._save_json(self.settings_path, data)

    async def change_channels_data(self, channels: List[str], path: str, new_data: bool):
        """Update channels data in JSON file"""
        data = self._load_json(path)
        for channel in channels:
            data[channel] = new_data
        self._save_json(path, data)

    async def handle_channel_message(self, client: Client, message: Message):
        """Handle incoming channel messages"""
        chat: Chat = message.sender_chat
        channel_name: str = chat.username
        channel_id: str = str(chat.id)

        self.load_settings()

        do_post = await self.should_post(
            channel_name,
            self.get_channels_number(),
            channel_id,
            multiplier=0
        )

        await self.repost(client, message, do_post)
        logger.info(f"{'POSTED' if do_post else 'NOT POSTED'} {channel_name} {channel_id}")

    def is_whitelisted(self, username: str) -> bool:
        """Check if channel is whitelisted"""
        data = self._load_json(self.data_path)
        return username in data and data[username]

    def get_stats(self, username: str) -> int:
        """Get channel statistics"""
        data = self._load_json(self.stats_path)
        return data.get(username, -1)

    def save_stats(self, username: str):
        """Save channel statistics"""
        data = self._load_json(self.stats_path)
        data[username] = int(datetime.timestamp(datetime.now()))
        self._save_json(self.stats_path, data)

    def is_channel_vip(self, channel_name: str) -> bool:
        """Check if channel is VIP"""
        data = self._load_json(self.vip_path)
        return channel_name in data and data[channel_name]

    def get_channels_number(self) -> int:
        """Get total number of channels"""
        if self.check_number == self.check_freq or self.check_number == -1:
            self.check_number = 0
            data = self._load_json(self.data_path)
            self.channels_number = list(data.values()).count(True)
        return self.channels_number

    def load_settings(self):
        """Load bot settings"""
        data = self._load_json(self.settings_path)
        self.multiplier = data.get("multiplier", 0)

    async def should_post(self, channel_name: str, channels_number: int,
                         channel_id: str, multiplier: int = 1000) -> bool:
        """Determine if message should be posted"""
        if not self.is_whitelisted(channel_name) and not self.is_whitelisted(channel_id):
            return False

        if self.is_channel_vip(channel_name):
            return True

        last_post = self.get_stats(channel_name)
        if last_post == -1:
            return True

        time_now = int(datetime.timestamp(datetime.now()))

        if time_now == last_post:
            return False

        chance = 1.0 - multiplier * channels_number / (time_now - last_post)
        logger.debug(f"Post chance: {chance}, Channel number: {channels_number}")

        if chance <= 0:
            return False
        return random() < chance

    async def repost(self, client: Client, message: Message, do_post: bool):
        """Repost message to target channel"""
        if not do_post:
            return

        try:
            caption = await self.generate_caption(message)

            if message.media_group_id:
                media_group = await client.get_media_group(message.chat.id, message.id)
                has_caption = any(msg.caption is not None for msg in media_group)

                if has_caption and not message.caption:
                    return

                async with self.posted_lock:
                    if self.posted.get(message.chat.id) == message.media_group_id:
                        logger.debug("Media group already posted")
                        return

                    await client.copy_media_group(
                        self.channel_id,
                        message.chat.id,
                        message_id=message.id,
                        captions=caption
                    )
                    self.posted[message.chat.id] = message.media_group_id

            else:
                if message.photo:
                    await client.send_photo(
                        self.channel_id,
                        message.photo.file_id,
                        caption=caption
                    )
                elif message.video:
                    await client.send_video(
                        self.channel_id,
                        message.video.file_id,
                        caption=caption
                    )
                elif message.text:
                    await client.send_message(
                        self.channel_id,
                        caption,
                        disable_web_page_preview=True
                    )
                else:
                    await client.forward_messages(
                        self.channel_id,
                        from_chat_id=message.chat.id,
                        message_ids=message.id
                    )

        except Exception as e:
            logger.error(f"Error in repost: {e}")
            self.sleep_time = 0

    @staticmethod
    def generate_hashtag(chat: Chat) -> str:
        """Generate hashtag from chat title"""
        name: str = chat.title if chat.title else chat.first_name
        name = name.replace(" ", "_")
        return "#" + "".join(c for c in name if c.isalnum() or c == "_")

    async def generate_caption(self, message: Message) -> str:
        """Generate caption for reposted message"""
        caption = message.caption.html if message.caption else (
            message.text.html if message.text else ""
        )

        real_id = str(message.chat.id)[4:] if str(
            message.chat.id).startswith("-100") else message.chat.id
        hashtag = self.generate_hashtag(message.chat)

        if message.forward_from_chat and message.forward_from_chat.username:
            caption += f"\n\nПереслано из: [{message.forward_from_chat.title}](https://t.me/c/{real_id}/{message.id})"

        caption += f"\n\nАвтор: [{message.chat.title}](https://t.me/c/{real_id}/{message.id})"
        caption += f" ({hashtag})"
        caption += "\n\n[Стена Иннополис. Подписаться.](https://t.me/+GC10Uk2uhnsyN2Y6)"

        return caption
