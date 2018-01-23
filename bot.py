import discord
import configparser

import asyncio
import requests
import json
import os

token = ''

if os.path.isfile('settings.config'):
    config = configparser.ConfigParser()
    config.read("settings.config")
    token = config.get("BOT_SETTINGS", 'token')

headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'}
affixes_url = "https://raider.io/api/v1/mythic-plus/affixes?region=us"


if token and token != '':
    client = discord.Client()
    @client.event
    async def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

    @client.event
    async def on_message(message):
        if message.content.startswith('!affix'):
            raw = requests.get(affixes_url, headers=headers, verify=False)
            page_data = json.loads(raw.content)
            affixes = page_data['title']
            await client.send_message(message.channel, 'This weeks affixes are: %s' % affixes)

        elif message.content.startswith('!mcsta'):
            await client.send_message(message.channel, 'Do. Not. Heal.')
    client.run(token)

else:
    print("You need to set your token in the settings.config file.")
    print("Rename the settings.config.example to settings.config and")
    print("set your token information.")
    print("Unsure of how to get a token?  Read this info:")
    print("https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token")
