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
                if now.weekday() == 1 and now.hour == 17 and now.minute == 00:
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
            max_renown=get_max_renown()
            wing_1, wing_2= get_torghast_wings()
            message='''**Good Morning!**

Happy Tuesday Defiant!

__Details for the week of %s/%s/%s__
```
Weekly Renown cap:  %s
Torghast wings open: %s, %s
```
The M+ affixes are...''' % (date_today.month, date_today.day, date_today.year,max_renown, wing_1, wing_2)
        except Exception as e:
            print("A thing broke: %s" % e)
            return message
        return message


    def calculate_weeks_since(start="06/22/2021"): #Default to start of expansion
        try:
            start_date  = datetime.datetime.strptime(start, '%m/%d/%Y')
            end_date    = datetime.datetime.today()
            week        = {}
            for i in range((end_date - start_date).days):
                day       = calendar.day_name[(start_date + datetime.timedelta(days=i+1)).weekday()]
                week[day] = week[day] + 1 if day in week else 1
            monday_count = week["Monday"]
        except Exception as e:
            bot_logger(message=e)
        return monday_count

    def get_torghast_wings():
        wing_1 = "Wing One"
        wing_2 = "Wing Two"
        wing_dict=({13400: "Skoldus Hall", 13403: "The Fracture Chambers", 13404: "The Soulforges", 13411: "Coldheart Interstitia", 13412: "Mort'regar", 13413: "The Upper Reaches"})
        try:
            raw = requests.get(wowhead_url, headers=headers, verify=False)
            soup = bs.BeautifulSoup(raw.text,'lxml')
            supa = soup.find('div',attrs={'id' : 'US-group-torghast-wings-line-0'})
            supb = soup.find('div',attrs={'id' : 'US-group-torghast-wings-line-1'})
            x = re.search('zone=([0-9]+)', str(supa))
            y = re.search('zone=([0-9]+)', str(supb))
            if x:
                wing_1 = wing_dict[int(x.group(1))]
            if y:
                wing_2 = wing_dict[int(y.group(1))]
        except Exception as e:
            bot_logger(message=e)
        return wing_1, wing_2

    def get_max_renown():
        max_renown = 1
        try:
            week = int(calculate_weeks_since())
            if week > 16:
                week=16
            renown={1:42,2:45,3:48,4:51,5:54,6:57,7:60,8:63,9:66,10:69,11:72,12:75,13:78,14:80}
            max_renown = renown[week]
        except Exception as e:
            bot_logger(message=e)
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
            bot_logger(message=e)
        return message_content

    def get_table(tableName):
        table = ''
        try:
            if tableName in ('chest', 'titan', 'mythic'):
                table = '''
`Mythic+ (Updated for 9.1)`
- Gear you will get per keystone level, and in your Great Vault after Tuesday reset.
```apache
  Key | iLvL End  | iLvL Vault
--------------------------------
   2  |    210    |    226
   3  |    213    |    226
   4  |    216    |    226
   5  |    220    |    229
   6  |    223    |    229
   7  |    223    |    233
   8  |    226    |    236
   9  |    226    |    236
   10 |    229    |    239
   11 |    229    |    242
   12 |    233    |    246
   13 |    233    |    246
   14 |    236    |    249
   15 |    239    |    252 ```
                '''

            elif tableName in ('ash'):
                table = '''
`Torghast (Updated for 9.1)`
- Each Layer in Torghast is 6 levels and different wings are open each week.
- NEW IN 9.1 - You can re-clear to farm ash. Try `!farmash` to see that chart. Soul Cinders are only earned once a week.
- Running the highest Layer you have unlocked awards all Soul Ash and Cinders for layers below it.
                ```apache
  Layer   | Ash + Cinders |    Total   |  Weekly
----------------------------------------------------
    1     |    180 + 0    | 180  + 0  |  360  + 0
    2     |    150 + 0    | 330  + 0  |  660  + 0
    3     |    130 + 0    | 460  + 0  |  920  + 0
    4     |    105 + 0    | 565  + 0  |  1130 + 0
    5     |    90  + 0    | 655  + 0  |  1310 + 0
    6     |    75  + 0    | 730  + 0  |  1460 + 0
    7     |    70  + 0    | 800  + 0  |  1600 + 0
    8     |    60  + 0    | 860  + 0  |  1720 + 0
    9     |    55  + 60   | 915  + 60 |  1830 + 120
    10    |    45  + 50   | 960  + 110|  1920 + 220
    11    |    40  + 40   | 1000 + 150|  2000 + 300
    12    |    30  + 30   | 1030 + 180|  2060 + 360
    ```
    '''

            elif tableName in ('farmash'):
                table = '''
`Torghast Re-Clear (Updated for 9.1)`
- You will get this exact amount for the clear, and will not get the layers below it.
                ```apache
  Layer   | Ash
-----------------
    1     | 36
    2     | 66
    3     | 92
    4     | 113
    5     | 131
    6     | 146
    7     | 160
    8     | 172
    9     | 183
    10    | 192
    11    | 200
    12    | 206
    ```
    '''
            elif tableName in ('valor'):
                table = '''
`Valor Points (Updated for 9.1)`

- Upgrade costs are based on the item slot.  Each rank costs the same amount for that slot regardless of ilvl.
                ```apache
 Cost   |  Item Slots
---------------------------------------------------
 250    |  Offhand, Ring, Cloak, Bracer, Neck
 400    |  Trinket, Belt, Shoulders, Gloves, Boots
 475    |  Helm, Legs, Chest
 500    |  One-Handed DPS Weapon
 750    |  One-Handed Int Weapon
 1000   |  Two-Handed Weapon


 Rank | iLvL | Rating Required
------------------------------
 1   |  210  | None
 2   |  213  | None
 3   |  216  | None
 4   |  220  | None
 5   |  223  | None
 6   |  226  | None
 7   |  229  | 750
 8   |  233  | 750
 9   |  236  | 1500
 10  |  239  | 1500
 11  |  242  | 2000
 12  |  246  | 2000
 ```
    '''


            elif tableName in ('leggo'):
                table = '''
`Building your Legendary (Updated for 9.1)`

- You can skip ranks when building, or upgrade from the previous rank.  Soul Ash costs are the same either way.
                ```apache
  Rank    |  iLvL  |  Ash  |  Upgrade Cost
--------------------------------------------
    1     |  190   |  1250 |  -
    2     |  210   |  2000 |  750
    3     |  225   |  3200 |  1200
    4     |  235   |  5150 |  1950
```
- No additional ash is needed to upgrade from 4, only cinders. Ash + Cinders is the total cost if building from scratch.
 ```apache
  Rank    |  iLvL  |  Ash + Cinders |  Upgrade Cost
----------------------------------------------------
    5     |  190   |  5150 + 400    |  0 + 400
    6     |  210   |  5150 + 1650   |  0 + 1250

```
'''
            elif tableName in ('timers'):
                table = '''
`Mythic + Timers`

- The timers for each M+
```json
   Dungeon               |  +1   |  +2   |  +3
-------------------------------------------------
   De Other Side         | 41:00 | 32:48 | 24:36
   Halls of Atonement    | 34:00 | 27:12 | 20:24
   Mists of Tirna Scithe | 30:00 | 24:00 | 18:00
   Necrotic Wake         | 32:00 | 25:36 | 19:12
   Plaguefall            | 38:00 | 30:24 | 22:48
   Sanguine Depths       | 41:00 | 32:48 | 24:36
   Spires of Ascension   | 36:00 | 28:48 | 21:36
   Theater of Pain       | 40:00 | 32:00 | 24:00 ```
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
            command_list = ['!affixes','!ash', '!soulash', '!cinder', '!vault', '!greatvault', '!chest', '!leggo', '!legendary', '!valor', '!logs', '!wings']
            command_list.sort()
            v = '''
`Help Menu`
**Some commands to try:** `%s`
            ''' % ('`, `'.join(command_list))
            await message.channel.send(v)

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

        elif message.content.lower().startswith('!chest') or message.content.lower().startswith('!titan') or message.content.lower().startswith('!resid') or message.content.lower().startswith('!mythic'):
            table = get_table("chest")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!leggo') or message.content.lower().startswith('!legendary') or message.content.lower().startswith('!lego'):
            table = get_table("leggo")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!ash') or message.content.lower().startswith('!soulash') or message.content.lower().startswith('!cinder'):
            table = get_table("ash")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!valor'):
            table = get_table("valor")
            await send_message(channel=message.channel, message=table, send_file=None)

        elif message.content.lower().startswith('!farmash'):
            table = get_table("farmash")
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

        elif message.content.lower().startswith('!wing'):
            wing_1, wing_2= get_torghast_wings()
            response = 'Wings open this week are %s and %s.' % (wing_1, wing_2)
            await send_message(channel=message.channel, message=response, send_file=None)

        elif message.content.lower().startswith('!restart'):
            author = message.author
            if str(author) in administrators:
                v="Restarting Discord Bot!"
                await send_message(channel=message.channel, message=v, send_file=None)
                close_discord()
            else:
                v = "Nope! %s"
                await send_message(channel=message.channel, message=v, send_file=None)

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
