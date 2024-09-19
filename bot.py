import discord
import configparser
import datetime
import calendar
import requests
import asyncio
import random
import pickle
import json
import ast
import os
import re
import bs4 as bs
import dadjokes

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
    administrators = config.get("BOT_SETTINGS", "administrators")

    if environment == 'PROD':
        error_channel = int(config.get("BOT_SETTINGS", "error_channel"))
        wow_channel = int(config.get("BOT_SETTINGS", 'wow_channel'))
        broadcast_channel = int(config.get("BOT_SETTINGS", 'broadcast_channel'))
        test_channel = int(config.get("BOT_SETTINGS", 'test_channel'))

    if environment == 'TEST':
        wow_channel = int(config.get("BOT_SETTINGS", 'test_channel'))
        broadcast_channel = int(config.get("BOT_SETTINGS", 'test_channel'))
        test_channel = int(config.get("BOT_SETTINGS", 'test_channel'))


headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'}
affixes_url = "https://raider.io/api/v1/mythic-plus/affixes?region=us"
buildings_url = "https://wow.gameinfo.io/broken-isles-buildings"
wowhead_url = "https://wowhead.com"

if token and token != '':
    client = discord.Client()
    @client.event
    async def on_ready():
        log = '''
Hello!  I just started.
Logged in as %s
With UserID %s
        ''' % (client.user.name, str(client.user.id))
        await bot_logger(message=log, log_type='info')
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

    def close_discord():
        try:
            exit()
        except Exception as e:
            bot_logger(message=e)

# --------------------- TIMED MESSAGES ---------------------
    #Tuesday morning announcements
    async def tuesday_morning_announces():
        try:
            await client.wait_until_ready()
            channel = client.get_channel(wow_channel)
            while True:
                now = datetime.datetime.now()
                if now.weekday() == 1 and now.hour == 19 and now.minute == 00:
                    tuesday_message = get_tuesday_message()
                    await bot_logger(message="Tuesday Announce Time", log_type="info")
                    await channel.send(tuesday_message)
                    message_content = get_affixes_message()
                    await channel.send(message_content)
                await asyncio.sleep(60) # task runs every 60 seconds
        except Exception as e:
            await bot_logger(message=e)

    client.loop.create_task(tuesday_morning_announces())


# --------------------- END TIMED MESSAGES ---------------------

# --------------------- HELPER METHODS ---------------------
    async def send_message(channel, message=None, send_file=None):
        try:
            if message and not send_file:
                await channel.send(message)
            elif send_file and not message:
                await channel.send(file=discord.File(send_file))
        except Exception as e:
            await bot_logger(message=e)

    async def bot_logger(message, log_type='error'):
        if log_type == 'error':
            message='''Error:
%s''' % str(message)
        elif log_type == 'info':
            message='''Info:
%s''' % str(message)
        channel=client.get_channel(error_channel)
        await send_message(channel=channel, message=message)

    def get_tuesday_message():
        message = '''Happy Tuesday Defiant!'''
        try:
            date_today = datetime.datetime.now()
            message='''**Good Morning!**

Happy Tuesday Defiant!

__Details for the week of %s/%s/%s__```

```The M+ affixes are...''' % (date_today.month, date_today.day, date_today.year)
        except Exception as e:
            print("A thing broke: %s" % e)
            return message
        return message


    def get_affixes_message():
        message_content = 'Something went wrong'
        try:
            raw = requests.get(affixes_url, headers=headers, verify=False)
            page_data = json.loads(raw.content)
            affixes = page_data['title']
            message_content = '''
                    **%s**  |  **%s**  |  **%s**  | **%s**

                    +2  - **%s** - %s
                    +4  - **%s** - %s
                    +7  - **%s** - %s
                    +10 - **%s** - %s
                    +12 - **Xal'atath's Guile** - All benefits from Xal'atath's Bargains are removed. All enemies have a flat 20% increase to their HP and damage
                    ''' % (page_data['affix_details'][0]['name'], page_data['affix_details'][1]['name'], page_data['affix_details'][2]['name'],page_data['affix_details'][3]['name'],
                        page_data['affix_details'][0]['name'], page_data['affix_details'][0]['description'],
                        page_data['affix_details'][1]['name'], page_data['affix_details'][1]['description'],
                        page_data['affix_details'][2]['name'], page_data['affix_details'][2]['description'],
                        page_data['affix_details'][3]['name'], page_data['affix_details'][3]['description']
                        )
        except Exception as e:
            bot_logger(message=e)
        return message_content

    def get_table(tableName):
        table = ''
        try:
            if tableName in ('chest', 'titan', 'mythic'):
                table = '''
`Season 1 Gear (Updated for 11.0.2)`
- Dungeon Loot Rewards At end of dungeon and Great Vault
```apache
  Key |  End  |   Track   | Vault | Track
-------------------------------------------
 Hero |  580  | Adven 4/8 |  593  | Vet 4/8
   0  |  597  | Champ 1/8 |  603  | Champ 3/8
   2  |  597  | Champ 1/8 |  606  | Champ 4/8
   3  |  597  | Champ 1/8 |  610  | Hero 1/6
   4  |  600  | Champ 2/8 |  610  | Hero 1/6
   5  |  603  | Champ 3/8 |  613  | Hero 2/6
   6  |  606  | Champ 4/8 |  613  | Hero 2/6
   7  |  610  | Hero 1/6  |  616  | Hero 3/6
   8  |  610  | Hero 1/6  |  619  | Hero 4/6
   9  |  613  | Hero 2/6  |  619  | Hero 4/6
   10 |  613  | Hero 2/6  |  623  | Myth 1/6```
   
- Bountiful Delve Rewards at end of run and Great Vault
```apache
  Lvl |  End  |   Track   | Vault | Track
-------------------------------------------
   1  |  561  | Expl 2/8  |  584  | Vet 1/8
   2  |  564  | Expl 3/8  |  584  | Vet 1/8
   3  |  571  | Adven 1/8 |  587  | Vet 2/8
   4  |  577  | Adven 3/8 |  597  | Champ 1/8
   5  |  584  | Vet 1/8   |  603  | Champ 3/8
   6  |  590  | Vet 3/6   |  606  | Champ 4/8
   7  |  597  | Champ 1/8 |  610  | Hero 1/6
   8+ |  603  | Champ 3/8 |  616  | Hero 3/6```
               
                '''

            elif tableName in ('timers'):
                table = '''
`Mythic+ Timers (Updated for 11.0.2)`

- The timers for each M+
```json
   Dungeon                    |  +1   |  +2   |  +3
------------------------------------------------------
   The Stonevault             | 33:00 | 24:26 | 19:48
   The Dawnbreaker            | 30:00 | 24:00 | 18:00
   City of Threads            | 35:00 | 29:00 | 21:00
   Ara-Kara, City of Echoes   | 30:40 | 24:00 | 18:00
   Mists of Tirna Scithe      | 30:00 | 24:00 | 18:00
   The Necrotic Wake          | 32:00 | 25:36 | 19:12
   Siege of Boralus           | 34:00 | 27:12 | 20:20
   Grim Batol                 | 36:00 | 29:12 | 21:36```
'''

        except Exception as e:
            bot_logger(message=e)
            return table
        return table

# --------------------- END HELPER METHODS ---------------------

# --------------------- CLIENT LISTENING METHODS ---------------------

    @client.event
    async def on_message(message):


        if message.content.lower().startswith('!help'):
            command_list = ['!chest', '!timers','!gear','!logs']
            command_list.sort()
            v = '''
`Help Menu`
**Some commands to try:** `%s`
            ''' % ('`, `'.join(command_list))
            await message.channel.send(v)

############# START USER SPECIFIC / FUN REACTIONS



        elif message.content.lower().startswith('!teo'):
            d = { 1 : 'Whisper that guy' , 2: 'Nicest guy in the guild.', 3: '''It's probably Teo's fault.'''}
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!tonkah') or message.content.lower().startswith('!taunk') or message.content.lower().startswith('!holy'):
            d = { 1 : '''https://memegenerator.net/img/instances/81499360/someone-say-my-name.jpg''', 2 : '''Dad jokes, inc.''' }
            if message.content.lower().startswith('!earth'):
                d = { 1 : '''The best healer ever, in warcraft, the world, and whatever else he needs to hear to heal.''', 2 : '''He is not listening.''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!eodred') or message.content.lower().startswith('!xorr'):
            await send_message(channel=message.channel, message=None, send_file='eodred.png')

############# END USER SPECIFIC / FUN REACTIONS

############# START SYSTEM ROLES
        elif message.content.lower().startswith('!roles'):
            v = '''Role Management

**-- Usage -- **
!role add roleName
!role remove roleName

**-- Current Roles Available -- **
lfg - Adds you to the wow-lfg channel if you are interested in notifications when people are looking to do stuff!
            '''
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!role'):
            content = message.content.lower()
            member = message.author
            role = False
            role_id = False
            action = "add"
            v = "Role not found!"
            if "add" in content:
                pass
            if "remove" in content:
                action = "remove"
            if "lfg" in content:
                role_name = "WoW LFG"
                role_id = 840351027127517195
            if role_id:
                role = discord.utils.get(message.guild.roles, id=role_id)

            if role:
                if action == "add":
                    v = "Adding the role [%s] to %s!" % (role_name, str(member))
                    await member.add_roles(role)
                elif action == "remove":
                    v = "Removing the role [%s] to %s!" % (role_name, str(member))
                    await member.remove_roles(role)
                await send_message(channel=message.channel, message=v, send_file=None)
            else:
                await send_message(channel=message.channel, message=v, send_file=None)

############# END SYSTEM ROLES


############# START SYSTEM REACTIONS

        elif message.content.lower().startswith('!chest') or message.content.lower().startswith('!vault') or message.content.lower().startswith('!gear') or message.content.lower().startswith('!mythic'):
            table = get_table("chest")
            await send_message(channel=message.channel, message=table, send_file=None)
            
        elif message.content.lower().startswith('!dadjoke'):
            dadjoke = dadjokes.Dadjoke()
            await send_message(channel=message.channel, message=dadjoke.joke, send_file=None)

        elif message.content.lower().startswith('!timer'):
            table = get_table("timers")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!logs'):
            d = { 1 : '''https://www.warcraftlogs.com/guild/us/doomhammer/defiant''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!mythiclogs'):
            d = { 1 : '''https://www.warcraftlogs.com/user/reports-list/401351/''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!tuesday'):
            tuesday_message = get_tuesday_message()
            await send_message(channel=message.channel, message=tuesday_message, send_file=None)
            message_content = get_affixes_message()
            await send_message(channel=message.channel, message=message_content, send_file=None)

        elif message.content.lower().startswith('!cmc'):
            mvals = message.content.split('|')
            print("mvals are %s" % mvals)
            mval_channel=discord.Object(id=int(mvals[1]))
            mval_message=mvals[2]
            await send_message(channel=mval_channel, message=mval_message, send_file=None)

        elif message.content.lower().startswith('!restart'):
            author = message.author
            if str(author) in administrators:
                v="Restarting Discord Bot!"
                await send_message(channel=message.channel, message=v, send_file=None)
                close_discord()
            else:
                v = "Nope! %s not a valid admin." % (str(author))
                await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!welcome'):
            author = message.author
            if str(author) in administrators:
                v = '''
***Welcome to Defiant!***
Before you click into the rest of the Discord here is some background on Defiant and some guidelines that help us remain a positive place for people to be and to hang out.

**About**
Defiant is a group of friends and family.

`WoW` - `Doomhammer / Baelgun` 
`New World` - `NA East - Nunne Chaha`

We are primarily adults and come from all walks of life.  Our core principle is putting people first.  We Raid, M+, PvP and quest together, but more importantly, become friends.  Community leadership is made up of a council who make decisions with the input from our officers and members.

**Success**
During WoW Raiding - Defiant consistently achieves the “Ahead of the Curve” achievement. We are not “hard-core” raiders, but we are serious about doing well and experiencing the content to the fullest. Consequently, we do not officially raid on mythic difficulty, as mythic raiding tends to require a more hard-core mindset and management style. As a Community we succeed by putting friendships and real life before video games, and treating each other with respect.

**Formula**
Key principles that have enabled such a longstanding and enjoyable community culture:
- We are a decidedly no-drama community. Keeping this in mind maintains a respectful and fun atmosphere.
- We respect and encourage different play-styles and intensities.
- Games are just games. Real life (RL) takes precedence in all situations.

**Guild Rules**
```
1.  No drama.
2.  Defiant is a family-friendly community. Swearing and lewd discussion is prohibited.
3.  Discrimination or derogatory discussion of age, sex, gender, race, religion, handicaps, sexual orientation, etc. is prohibited.
4.  Discussion of drama-prone topics, such as politics or religion, etc. should be avoided.
5.  Do not petition community members for gold, carries, gear, materials, or boosted runs.
6.  Pants are optional, and never enforced.```
'''
                await send_message(channel=message.channel, message=v, send_file=None)

# --------------------- END CLIENT LISTENING METHODS ---------------------77946686891425797

    #Start the client
    client.run(token)

else:
    print("You need to set your token in the settings.config file.")
    print("Rename the settings.config.example to settings.config and")
    print("set your token information.")
    print("Unsure of how to get a token?  Read this info:")
    print("https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token")
