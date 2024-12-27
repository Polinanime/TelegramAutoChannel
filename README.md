# Telegram Auto Channel

A Python-based Telegram bot that automatically reposts content from multiple source channels to a target channel with customizable features and content management.

You can explore the bot's functionality bby checking out the [demo channel](https://t.me/inno_wall).

## Features

- Automatic reposting from whitelisted channels
- VIP channel support with priority posting
- Media group handling (albums)
- Custom caption generation with source attribution
- Rate limiting and post frequency control
- Command-based channel management

## Setup

### Prerequisites

- Python 3.9+
- Telegram API credentials (api_id and api_hash)
- Docker (optional)

### Installation

1. Clone the repository:

```bash bash
git clone [repository-url]
cd telegram-auto-channel
```

2. Install dependencies:

```bash bash
pip install -r requirements.txt
```

3. Configure your settings:
   - Create `data/settings.json` with your configuration
   - Set up your channel lists in `data/referenceChannels.json` and `data/priorityChannels.json`

### Configuration Files

- `settings.json`: Basic bot settings including multiplier
- `referenceChannels.json`: List of whitelisted channels
- `priorityChannels.json`: List of VIP channels with priority posting
- `stats.json`: Automatically generated posting statistics

## Usage

### Bot Commands

All commands use the `%%` prefix and are only available in saved-messages-chat:

- `%%add [channel]` - Add channel to whitelist
- `%%remove [channel]` - Remove channel from whitelist
- `%%vip [channel]` - Add channel to VIP list
- `%%unvip [channel]` - Remove channel from VIP list
- `%%mult [number]` - Set posting frequency multiplier
- `%%ping` - Check if bot is running

### Running the Bot

Using Python:

```bash
python main.py
```

Using Docker:

```bash
docker-compose up --build
```

## Features Description

### Channel Management

- Whitelist system for controlling source channels
- VIP channel system for priority posting
- Automatic post frequency management

### Content Handling

- Supports text, photos, videos, and media groups
- Automatic caption generation with source attribution
- Maintains original media quality
- Handles forwarded messages

### Post Control

- Smart posting algorithm based on channel activity
- Configurable posting frequency
- Duplicate prevention for media groups

## Contributing

Feel free to submit issues and enhancement requests!

## Note

This bot is designed for channel management and should be used in accordance with Telegram's Terms of Service and API guidelines.
