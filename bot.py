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

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

system_commands_db = 'system_commands_db.pkl'
user_messages = 'user_messages.pkl'
error_channel = 789176146444812300

if os.path.isfile('settings.config'):
    config = configparser.ConfigParser()
    config.read("settings.config")
    environment = config.get("BOT_SETTINGS", 'environment')
    token = config.get("BOT_SETTINGS", 'token')
    base_directory = config.get("BOT_SETTINGS", 'base_directory')
    administrators = config.get("BOT_SETTINGS", "administrators")

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

    def close_discord():
        try:
            exit()
        except Exception as e:
            print("Something went wrong: %s" % e)

# --------------------- TIMED MESSAGES ---------------------
    #Tuesday morning announcements
    async def tuesday_morning_announces():
        await client.wait_until_ready()
        channel = client.get_channel(wow_channel)
        max_renown = get_max_renown()
        tuesday_message = get_tuesday_message()
        while not client.is_closed:
            now = datetime.datetime.now()
            if now.weekday() == 1 and now.hour == 9 and now.minute == 15:
                await channel.send(tuesday_message)
                message_content = get_affixes_message()
                await channel.send(message_content)
            await asyncio.sleep(60) # task runs every 60 seconds

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
            print("Sending message went wrong: %s" % e)

    def log_bot_error(message):
        channel=client.get_channel(error_channel)
        await send_message(channel=channel, message=message)

    def get_tuesday_message():
        message = '''Happy Tuesday Defiant!'''
        wing_1 = "Wing One"
        wing_2 = "Wing Two"
        try:
            date_today = datetime.datetime.now()
            max_renown=get_max_renown()
            message='''**Good Morning!**

Happy Tuesday Defiant!

__Details for the week of %s/%s/%s__
```
Weekly Renown cap:  %s
Torghast wings open: %s, %s *(coming soon)*
```
The M+ affixes are...''' % (date_today.month, date_today.day, date_today.year,max_renown, wing_1, wing_2)
        except Exception as e:
            print("A thing broke: %s" % e)
            return message
        return message


    def calculate_weeks_since(start="11/22/2020"): #Default to start of expansion
        try:
            start_date  = datetime.datetime.strptime(start, '%m/%d/%Y')
            end_date    = datetime.datetime.today()
            week        = {}
            for i in range((end_date - start_date).days):
                day       = calendar.day_name[(start_date + datetime.timedelta(days=i+1)).weekday()]
                week[day] = week[day] + 1 if day in week else 1
            monday_count = week["Monday"]
        except Exception as e:
            return "Something went poorly: %s" % (str(e))
        return monday_count


    def get_max_renown():
        max_renown = 1
        try:
            week = int(calculate_weeks_since())
            if week > 16:
                week=16
            renown={1:3,2:6,3:9,4:12,5:15,6:18,7:22,8:24,9:26,10:28,11:30,12:32,13:34,14:36,15:38,16:40}
            max_renown = renown[week]
        except Exception as e:
            print("Something went wrong: %s" % e)
        return max_renown

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

    def get_table(tableName):
        table = ''
        try:
            if tableName in ('chest', 'titan', 'mythic'):
                table = '''
`Mythic +`

- Gear you will get per keystone level, and in your Great Vault after Tuesday reset.
```apache
  Key | iLvL End  | iLvL Vault
--------------------------------
   2  |    187    |    200
   3  |    190    |    203
   4  |    194    |    207
   5  |    194    |    210
   6  |    197    |    210
   7  |    200    |    213
   8  |    200    |    216
   9  |    200    |    216
   10 |    204    |    220
   11 |    204    |    220
   12 |    207    |    223
   13 |    207    |    223
   14 |    207    |    226
   15 |    210    |    226 ```
                '''

            elif tableName in ('ash'):
                table = '''
`Torghast`

- Each Layer in Torghast is 6 levels and wings are open each week.
- You can only get the Ash from each wing/layer once per week.
- Running the highest Layer you have unlocked awards all Soul Ash for layers below it. Skipping right to layer 8 awards the full 570 Soul Ash.
                ```apache
  Layer   | Soul Ash  |  Total  |  Weekly Cap
----------------------------------------------
    1     |    120    |  120    |  240
    2     |    100    |  220    |  440
    3     |    85     |  305    |  610
    4     |    70     |  375    |  750
    5     |    60     |  435    |  870
    6     |    50     |  485    |  970
    7     |    45     |  530    |  1060
    8     |    40     |  570    |  1140```
    '''

            elif tableName in ('leggo'):
                table = '''
`Building your Legendary`

- You can skip ranks when building, or upgrade from the previous rank.  Soul Ash costs are the same either way.
                ```apache
  Rank    |  iLvL  |  Ash  |  Upgrade Cost
--------------------------------------------
    1     |  190   |  1250 |  -
    2     |  210   |  2000 |  750
    3     |  225   |  3200 |  1200
    4     |  235   |  5150 |  1950
```
'''
            elif tableName in ('timers'):
                table = '''
`Mythic + Timers`

- The timers for each M+
```json
   Dungeon               |  +1   |  +2   |  +3
-------------------------------------------------
   De Other Side         | 37:00 | 29:36 | 22:12
   Halls of Atonement    | 34:00 | 27:12 | 20:24
   Mists of Tirna Scithe | 30:00 | 24:00 | 18:00
   Necrotic Wake         | 32:00 | 25:36 | 19:12
   Plaguefall            | 38:00 | 30:24 | 22:48
   Sanguine Depths       | 41:00 | 32:48 | 24:36
   Spires of Ascension   | 36:00 | 28:48 | 21:36
   Theater of Pain       | 40:00 | 32:00 | 24:00 ```
'''

        except Exception as e:
            logger.error('Error REPLACE Message: %s' % (e))
            return table
        return table

# --------------------- END HELPER METHODS ---------------------

# --------------------- CLIENT LISTENING METHODS ---------------------

    @client.event
    async def on_message(message):


        if message.content.lower().startswith('!help'):
            await message.channel.send('''
                `Help Menu`

Some commands to try:
```CSS
!affixes, !logs, !chest, !ash, !soulash, !legendary, !leggo, !vault, !greatvault```
                '''
                )

############# START USER SPECIFIC / FUN REACTIONS

        elif message.content.lower().startswith('!whatday'):
            d = { 1 : '''https://strats-forum-attachments.s3.amazonaws.com/original/2X/5/5c98f26aa5468db7870865429ea404ea32131f67.jpg''', 2 : '''https://i.imgur.com/x0qSq5H.png''', 3 : '''https://memegenerator.net/img/instances/56758076/did-someone-say-raid-night.jpg''', 4 : '''http://s.quickmeme.com/img/18/18c2f6010e5e9cd3c2b868785cfe6628788beff0f46f89c83b2c55cbae7c1502.jpg''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!ball'):
            d = { 1 : '''It wasn't me.''', 2 : '''Don't worry, this portal is safe. :D ''', 3 : 'https://media1.tenor.com/images/9cd51c012a19b1ed7501f7fee83e9617/tenor.gif', 4: '''https://media.tenor.com/images/077234833a766b534f348213f742eaf0/tenor.gif''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!mcsta'):
            d = { 1 : '..you can fall of this ledge guys.', 2 : 'Do. Not. Heal.', 3 : 'TEAM RAMROD!', 4: '''https://i.pinimg.com/originals/82/da/70/82da703541a8b54d123650e4829a5edb.jpg''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!walm'):
            d = { 1 : '1 Plz.', 2 : '''https://i.imgflip.com/2uvz1e.jpg''', 3 : 'Another 1 plz, lol I canceled that one.', 4 : '''https://i.imgflip.com/2uvzyi.jpg'''}
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!rez'):
            d = { 1 : 'https://memegenerator.net/img/instances/81499260/heeeeeyyyyooooooo.jpg', 2 : 'Them bearwinders though.', 3 : 'https://memegenerator.net/img/instances/81499241/beeeooo-beeeooo-beeeooo-beeeooo-beeeooo-beeeooooooo.jpg', 4 : "Don't worry, it'll just be a quick plus-a-roo" }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!shept'):
            d = { 1 : 'Very punny guy!', 2 : 'The robot version is the best version.', 3 : 'Prot DPS spec!', 4 : 'Agreed. Everyone should roll paladins.' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!lon'):
            d = { 1 : 'WHAT DAY IS IT!?!?', 2 : 'Lootsham? Looticus?', 3 : 'All your loot are belong to him.'}
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!scarab'):
            d = { 1 : 'Sleepy Boy!', 2 : 'That dead shaman over there?', 3 : '''Top DPS? Dead? Asleep? Anyone's guess really.''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!nia'):
            d = { 1 : 'Watch. Your. Throat.' , 2: 'Too many chiefs!', 3: '''You're not the boss of me.'''}
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!teo'):
            d = { 1 : 'Whisper that guy' , 2: 'Nicest guy in the guild.', 3: '''It's probably Teo's fault.'''}
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!tareva'):
            d = { 1 : '...  <-- a joke about being really quiet.' , 2: 'The actual guild leader.  Pulling strings behind the scenes.'}
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!shy'):
            d = { 1 : '''Hey it's Mosh.... Shyrene!!''', 2 : '''Steal some of Lonsham's luck for us already''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!darj'):
            d = { 1 : '''He's got moon''', 2 : '''10 minute break?  Sweet.  Be back in 20.''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!token'):
            d = { 1 : '''https://memegenerator.net/img/instances/81499276/have-you-heard-of-this-thing-the-netherlight-crucible.jpg''', 2 : '''https://memegenerator.net/img/instances/81499311/inc-bud.jpg''' }
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

        elif message.content.lower().startswith('!mag'):
            await send_message(channel=message.channel, message=None, send_file='magnollia.png')

        elif message.content.lower().startswith('!sour'):
            d = { 1 : '''Hold on, hold on, hold on... wait... Reznik, what is the button called that I push to taunt?''', 2 : '''Cracklin' with lightning?  Friend huggin' time.''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!rath'):
            await send_message(channel=message.channel, message=None, send_file='rathattack.png')

############# END USER SPECIFIC / FUN REACTIONS

############# START SYSTEM REACTIONS

        elif message.content.lower().startswith('!chest') or message.content.lower().startswith('!titan') or message.content.lower().startswith('!resid') or message.content.lower().startswith('!mythic'):
            table = get_table("chest")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!leggo') or message.content.lower().startswith('!legendary'):
            table = get_table("leggo")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!ash') or message.content.lower().startswith('!soulash'):
            table = get_table("ash")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!timer'):
            table = get_table("timers")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!affix'):
            await send_message(channel=message.channel, message=None, send_file='affixes.png')

        elif message.content.lower().startswith('!logs'):
            d = { 1 : '''https://www.warcraftlogs.com/guild/us/doomhammer/defiant''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!mythiclogs'):
            d = { 1 : '''https://www.warcraftlogs.com/user/reports-list/401351/''' }
            k, v = random.choice(list(d.items()))
            await send_message(channel=message.channel, message=v, send_file=None)

        elif message.content.lower().startswith('!tuesday'):
            max_renown = get_max_renown()
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

        elif message.content.lower().startswith('!vault') or message.content.lower().startswith('!greatvault') or message.content.lower().startswith('!gv'):
            await send_message(channel=message.channel, message=None, send_file='gv.png')

        elif message.content.lower().startswith('!renown'):
            max_renown = get_max_renown()
            response = 'Current Renown Cap: %s' % str(max_renown)
            await send_message(channel=message.channel, message=response, send_file=None)

        elif message.content.lower().startswith('!restart'):
            author = message.author
            if str(author) in administrators:
                v="Restarting Discord Bot!"
                await send_message(channel=message.channel, message=v, send_file=None)
                close_discord()

        elif message.content.lower().startswith('!error'):
            author = message.author
            if str(author) in administrators:
                v="This is an error log!"
                log_bot_error(message=v)

        elif message.content.lower().startswith('!welcome'):
            author = message.author
            if str(author) in administrators:
                v = '''
***Welcome to Defiant! We are glad that you are here!***

Before you click into the rest of the Discord here is some background on Defiant and some guidelines that help us remain a positive place for people to be and to hang out.

**About**
Defiant is a group of friends and family on the Doomhammer / Baelgun playing since the days of Vanilla WoW.  We are primarily adults and come from all walks of life.  Our core principle is putting people first.  We Raid, M+, PvP and quest together, but more importantly, become friends.  Guild leadership is made up of a council of GMs making decisions with the input from our officers and members.

**Success**
Defiant consistently achieves the “Ahead of the Curve” achievement while raiding. We are not “hard-core” raiders, but we are serious about doing well and experiencing the content to the fullest. Consequently, we do not officially raid on mythic difficulty, as mythic raiding tends to require a more hard-core mindset and management style.

**Formula**
There are a few key principles that have enabled such a longstanding and enjoyable guild culture.
- We are a decidedly no-drama guild. Keeping this in mind maintains a respectful and fun atmosphere.
- We respect and encourage different play-styles and intensities.
- WoW is a game. Real life (RL) takes precedence in all situations.

**Guild Rules**
```
1.  No drama.
2.  Defiant is a family-friendly guild. Swearing and lewd discussion is prohibited.
3.  Discrimination or derogatory discussion of age, sex, gender, race, religion, handicaps, sexual orientation, etc. is prohibited.
4.  Discussion of drama-prone topics, such as politics or religion, etc. should be avoided.
5.  Do not petition guild members for gold, carries, gear, materials, or boosted runs.
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
