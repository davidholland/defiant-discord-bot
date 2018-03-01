import discord
import configparser
import datetime
import asyncio
import requests
import json
import ast
import os
import re

token = ''

if os.path.isfile('settings.config'):
    config = configparser.ConfigParser()
    config.read("settings.config")
    environment = config.get("BOT_SETTINGS", 'environment')
    token = config.get("BOT_SETTINGS", 'token')

    if environment == 'PROD':
        wow_channel = config.get("BOT_SETTINGS", 'wow_channel')
        broadcast_channel = config.get("BOT_SETTINGS", 'broadcast_channel')
        test_channel = config.get("BOT_SETTINGS", 'test_channel')

    if environment == 'TEST':
        wow_channel = config.get("BOT_SETTINGS", 'test_channel')
        broadcast_channel = config.get("BOT_SETTINGS", 'test_channel')
        test_channel = config.get("BOT_SETTINGS", 'test_channel')



headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'}
affixes_url = "https://raider.io/api/v1/mythic-plus/affixes?region=us"
buildings_url = "https://wow.gameinfo.io/broken-isles-buildings"


if token and token != '':
    client = discord.Client()
    @client.event
    async def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

# --------------------- TIMED MESSAGES ---------------------

    async def tuesday_morning_announces():
        await client.wait_until_ready()
        channel = discord.Object(id=wow_channel)
        while not client.is_closed:
            now = datetime.datetime.now()
            if now.weekday() == 2 and now.hour == 9 and now.minute == 45:
                await client.send_message(channel, '''Happy Tuesday Defiant! This weeks affixes are...  ''')
                message_content = get_affixes_message()
                await client.send_message(channel, message_content)
            await asyncio.sleep(60) # task runs every 60 seconds

    client.loop.create_task(tuesday_morning_announces())


# --------------------- END TIMED MESSAGES ---------------------

# --------------------- SUPPORTING METHODS ---------------------

    def get_affixes_message():
        message_content = 'Something went wrong'
        try:
            raw = requests.get(affixes_url, headers=headers, verify=False)
            page_data = json.loads(raw.content)
            affixes = page_data['title']
            message_content = '''Got it!

                    **%s**  |  **%s**  |  **%s**

                    **%s** - %s
                    **%s** - %s
                    **%s** - %s
                    ''' % (page_data['affix_details'][0]['name'], page_data['affix_details'][1]['name'], page_data['affix_details'][2]['name'],
                        page_data['affix_details'][0]['name'], page_data['affix_details'][0]['description'],
                        page_data['affix_details'][1]['name'], page_data['affix_details'][1]['description'],
                        page_data['affix_details'][2]['name'], page_data['affix_details'][2]['description']
                        )
        except Exception as e:
            print("Something went wrong: %s" % e)

        return message_content

    def get_building_progress():
        raw = requests.get(buildings_url, headers=headers, verify=False)
        match = re.search(r'{\"US\":(.*?}})', raw.content.decode('utf-8'))
        build_range = match[1]
        build_dict = ast.literal_eval(match[1])
        mage_tower = build_dict['1']['contributed']
        command_center = build_dict['2']['contributed']
        nether_disruptor = build_dict['3']['contributed']

        return mage_tower, command_center, nether_disruptor





# --------------------- END SUPPORTING METHODS ---------------------

# --------------------- CLIENT LISTENING METHODS ---------------------

    @client.event
    async def on_message(message):
        if message.content.startswith('!affix'):
            await client.send_message(message.channel, '''Let's find out what junk we are dealing with this week...''')
            message_content = get_affixes_message()
            await client.send_message(message.channel, message_content)

        elif message.content.startswith('!mcsta'):
            await client.send_message(message.channel, 'Do. Not. Heal.')

        elif message.content.startswith('!build'):
            mage_tower, command_center, nether_disruptor = get_building_progress()
            await client.send_message(message.channel, ''' Current Building Progress:

               **Mage Tower** - %s%%
               **Command Center** - %s%%
               **Nether Disruptor** - %s%%

                ''' % (mage_tower, command_center, nether_disruptor)
                )

# --------------------- END CLIENT LISTENING METHODS ---------------------

    #Start the client
    client.run(token)


else:
    print("You need to set your token in the settings.config file.")
    print("Rename the settings.config.example to settings.config and")
    print("set your token information.")
    print("Unsure of how to get a token?  Read this info:")
    print("https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token")
