import discord
import configparser
import datetime
import requests
import asyncio
import random
import pickle
import json
import ast
import os
import re

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

system_commands_db = 'system_commands_db.pkl'
user_messages = 'user_messages.pkl'

if os.path.isfile('settings.config'):
    config = configparser.ConfigParser()
    config.read("settings.config")
    environment = config.get("BOT_SETTINGS", 'environment')
    token = config.get("BOT_SETTINGS", 'token')
    base_directory = config.get("BOT_SETTINGS", 'base_directory')

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
    #Tuesday morning announcements
    async def tuesday_morning_announces():
        await client.wait_until_ready()
        channel = discord.Object(id=wow_channel)
        while not client.is_closed:
            now = datetime.datetime.now()
            if now.weekday() == 1 and now.hour == 9 and now.minute == 15:
                await client.send_message(channel, '''Happy Tuesday Defiant! This weeks affixes are...  ''')
                message_content = get_affixes_message()
                await client.send_message(channel, message_content)
            await asyncio.sleep(60) # task runs every 60 seconds

    client.loop.create_task(tuesday_morning_announces())


# --------------------- END TIMED MESSAGES ---------------------

# --------------------- LOOPS ---------------------
    # Monitor the broken shore buildings and announce completion
    async def building_state_monitor():
        mt_percent_start, cc_percent_start, nd_percent_start, mt_state_start, cc_state_start, nd_state_start = get_building_progress()
        await client.wait_until_ready()
        channel = discord.Object(id=wow_channel)
        while not client.is_closed:
            mt_percent, cc_percent, nd_percent, mt_state, cc_state, nd_state = get_building_progress()

            if mt_state == 'Complete!' and mt_state_start != 'Complete!':
                await client.send_message(channel, '''Hey guys, I just wanted you to know that the Mage Tower is complete on the Broken Shore! ''')
            mt_state_start = mt_state

            if cc_state == 'Complete!' and cc_state_start != 'Complete!':
                await client.send_message(channel, '''Dear friends: the Command Center is complete on the Broken Shore! ''')
            cc_state_start = cc_state

            if nd_state == 'Complete!' and nd_state_start != 'Complete!':
                await client.send_message(channel, '''Alert! Alert! The Nether Disruptor is complete on the Broken Shore! ''')
            nd_state_start = nd_state

            await asyncio.sleep(300) # task runs every 5 minutes

    client.loop.create_task(building_state_monitor())

# --------------------- END LOOPS ---------------------


# --------------------- HELPER METHODS ---------------------

    def get_affixes_message():
        message_content = 'Something went wrong'
        try:
            raw = requests.get(affixes_url, headers=headers, verify=False)
            page_data = json.loads(raw.content)
            affixes = page_data['title']
            message_content = '''
                    **%s**  |  **%s**  |  **%s**  |  **%s**

                    **%s** - %s
                    **%s** - %s
                    **%s** - %s
                    **%s** - %s
                    ''' % (page_data['affix_details'][0]['name'], page_data['affix_details'][1]['name'], page_data['affix_details'][2]['name'], page_data['affix_details'][3]['name'],
                        page_data['affix_details'][0]['name'], page_data['affix_details'][0]['description'],
                        page_data['affix_details'][1]['name'], page_data['affix_details'][1]['description'],
                        page_data['affix_details'][2]['name'], page_data['affix_details'][2]['description'],
                        page_data['affix_details'][3]['name'], page_data['affix_details'][3]['description']
                        )
        except Exception as e:
            print("Something went wrong: %s" % e)
        return message_content

    def get_building_progress():

        def get_state_translation(state_number):
            state = 'Unknown'
            if state_number == 1:
                state = 'Under Construction'
            elif state_number == 2:
                state = 'Complete!'
            elif state_number == 3:
                state = 'Under Attack'
            return state

        raw = requests.get(buildings_url, headers=headers, verify=False)
        match = re.search(r'{\"US\":(.*?}})', raw.content.decode('utf-8'))
        clean_match = match[1].replace("null", "0")
        build_dict = ast.literal_eval(clean_match)

        #Mage Tower Info
        mt_state = get_state_translation(build_dict['1']['state'])
        mt_percent = build_dict['1']['contributed']
        #Command Center Info
        cc_state = get_state_translation(build_dict['2']['state'])
        cc_percent = build_dict['2']['contributed']
        #Nether Disruptor Info
        nd_state = get_state_translation(build_dict['3']['state'])
        nd_percent = build_dict['3']['contributed']


        return mt_percent, cc_percent, nd_percent, mt_state, cc_state, nd_state


# --------------------- END HELPER METHODS ---------------------

# --------------------- CLIENT LISTENING METHODS ---------------------

    @client.event
    async def on_message(message):


        if message.content.lower().startswith('!help'):
            await client.send_message(message.channel, '''I'm a work in progress - if there's anything you like to see me be able to do talk to Eodred.
                Defiant website: http://thedefiantguild.com/

                I currently respond to the following commands:  !affix, !build, !help, !logs, !chest, !titan, !timers
                There might be a few hidden ones.  We'll see.
                '''
                )
        # Channel command to handle affixes
        elif message.content.lower().startswith('!affix'):
            await client.send_message(message.channel, '''Let's find out what junk we are dealing with this week...''')
            message_content = get_affixes_message()
            await client.send_message(message.channel, message_content)

        # Channel command to handle build status
        elif message.content.lower().startswith('!build'):
            mt_percent, cc_percent, nd_percent, mt_state, cc_state, nd_state = get_building_progress()
            await client.send_message(message.channel, ''' Current Building Progress:

               Mage Tower is %s - %s%%
               Command Center is %s - %s%%
               Nether Disruptor %s - %s%%

                ''' % (mt_state, mt_percent, cc_state, cc_percent, nd_state, nd_percent)
                )


        elif message.content.lower().startswith('!whatday'):
            d = { 1 : '''https://strats-forum-attachments.s3.amazonaws.com/original/2X/5/5c98f26aa5468db7870865429ea404ea32131f67.jpg''', 2 : '''https://i.imgur.com/x0qSq5H.png''', 3 : '''https://memegenerator.net/img/instances/56758076/did-someone-say-raid-night.jpg''', 4 : '''http://s.quickmeme.com/img/18/18c2f6010e5e9cd3c2b868785cfe6628788beff0f46f89c83b2c55cbae7c1502.jpg''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!ball'):
            d = { 1 : '''It wasn't me.''', 2 : '''Don't worry, this portal is safe. :D ''', 3 : 'https://media1.tenor.com/images/9cd51c012a19b1ed7501f7fee83e9617/tenor.gif', 4: '''https://media.tenor.com/images/077234833a766b534f348213f742eaf0/tenor.gif''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!mcsta'):
            d = { 1 : '..you can fall of this ledge guys.', 2 : 'Do. Not. Heal.', 3 : 'TEAM RAMROD!', 4: '''https://i.pinimg.com/originals/82/da/70/82da703541a8b54d123650e4829a5edb.jpg''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!walm'):
            d = { 1 : '1 Plz.', 2 : '''https://i.imgflip.com/2uvz1e.jpg''', 3 : 'Another 1 plz, lol I canceled that one.', 4 : '''https://i.imgflip.com/2uvzyi.jpg'''}
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!rez'):
            d = { 1 : 'https://memegenerator.net/img/instances/81499260/heeeeeyyyyooooooo.jpg', 2 : 'Them bearwinders though.', 3 : 'https://memegenerator.net/img/instances/81499241/beeeooo-beeeooo-beeeooo-beeeooo-beeeooo-beeeooooooo.jpg', 4 : "Don't worry, it'll just be a quick plus-a-roo" }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!shept'):
            d = { 1 : 'Very punny guy!', 2 : 'The robot version is the best version.', 3 : 'Prot DPS spec!', 4 : 'Agreed. Everyone should roll paladins.' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!lon'):
            d = { 1 : 'WHAT DAY IS IT!?!?', 2 : 'Lootsham? Looticus?', 3 : 'All your loot are belong to him.'}
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!scarab'):
            d = { 1 : 'Sleepy Boy!', 2 : 'That dead shaman over there?', 3 : '''Top DPS? Dead? Asleep? Anyone's guess really.''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!nia'):
            d = { 1 : 'Watch. Your. Throat.' , 2: 'Too many chiefs!', 3: '''You're not the boss of me.'''}
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!teo'):
            d = { 1 : 'Whisper that guy' , 2: 'Nicest guy in the guild.', 3: '''It's probably Teo's fault.'''}
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!tareva'):
            d = { 1 : '...  <-- a joke about being really quiet.' , 2: 'The actual guild leader.  Pulling strings behind the scenes.'}
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!shy'):
            d = { 1 : '''Hey it's Mosh.... Shyrene!!''', 2 : '''Steal some of Lonsham's luck for us already''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!darj'):
            d = { 1 : '''He's got moon''', 2 : '''10 minute break?  Sweet.  Be back in 20.''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!token'):
            d = { 1 : '''https://memegenerator.net/img/instances/81499276/have-you-heard-of-this-thing-the-netherlight-crucible.jpg''', 2 : '''https://memegenerator.net/img/instances/81499311/inc-bud.jpg''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!tonkah') or message.content.lower().startswith('!taunk') or message.content.lower().startswith('!holy'):
            d = { 1 : '''https://memegenerator.net/img/instances/81499360/someone-say-my-name.jpg''', 2 : '''Dad jokes, inc.''' }
            if message.content.lower().startswith('!earth'):
                d = { 1 : '''The best healer ever, in warcraft, the world, and whatever else he needs to hear to heal.''', 2 : '''He is not listening.''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!eodred') or message.content.lower().startswith('!xorr'):
            d = { 1 : '''https://memegenerator.net/img/instances/81499486/did-we-hit-every-bomb-on-that-bridge.jpg''', 2 : '''https://memegenerator.net/img/instances/81499514/mmmhhmmm.jpg''', 3: '''*sigh*''' }
            if message.content.lower().startswith('!xorr'):
                d = { 1: '''https://i.pinimg.com/originals/fc/14/a3/fc14a3c0632ed3b8ce06c8cae0d43ace.gif'''}
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!sour'):
            d = { 1 : '''Hold on, hold on, hold on... wait... Reznik, what is the button called that I push to taunt?''', 2 : '''Cracklin' with lightning?  Friend huggin' time.''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!chest'):
            d = { 1 : '''https://www.wowhead.com/mythic-keystones-and-dungeons-guide#other-gear-item-levels''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!timer'):
            d = { 1 : '''https://www.wowhead.com/mythic-keystones-and-dungeons-guide#dungeon-timers'''}
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!titan'):
            d = { 1 : '''https://www.wowhead.com/mythic-keystones-and-dungeons-guide#titan-resdiuum''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!logs'):
            d = { 1 : '''https://www.warcraftlogs.com/guild/us/doomhammer/defiant''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)

        elif message.content.lower().startswith('!mythiclogs'):
            d = { 1 : '''https://www.warcraftlogs.com/user/reports-list/401351/''' }
            k, v = random.choice(list(d.items()))
            await client.send_message(message.channel, v)




# --------------------- END CLIENT LISTENING METHODS ---------------------

    #Start the client
    client.run(token)


else:
    print("You need to set your token in the settings.config file.")
    print("Rename the settings.config.example to settings.config and")
    print("set your token information.")
    print("Unsure of how to get a token?  Read this info:")
    print("https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token")
