import discord
import database
import info
import sqlite3
import github3
from discord.ext import commands
import asyncio
import time
import datetime
from info import username, password
from github3 import create_gist

gh = github3.login(username, password=password)
bot = commands.Bot(command_prefix='!', description="I am the RuP bot!")

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def test():
    await bot.say("Hello", tts=True)


# !addReminder <group> <endTimeDate> <message>
async def addReminder(message):
    conn, cur = database.get()

    msg = message.content

    tokens = msg.split(' ')
    group, endTimeDate = tokens[1], tokens[2]
    reminderText = ' '.join(tokens[3:])

    timeStamp = time.mktime(datetime.datetime.strptime(endTimeDate, "%d/%m/%Y/%H:%M").timetuple())

    with conn:
        conn.execute("INSERT INTO Reminders ('reminderText', 'endTime', 'authorName', 'discordId', 'targetedGroup') VALUES (?, ?, ?, ?, ?)",
                     (reminderText, timeStamp, str(message.author), str(message.author.id), group))

    await bot.send_message(message.channel, "Reminder successfully added.")


@bot.command()
async def finishReminder(id: int):
    conn, cur = database.get()

    with conn:
        cur.execute(
            'UPDATE Reminders set finished = 1 WHERE id = {}'.format(id))

async def announcement():
    await bot.wait_until_ready()
    channel = discord.Object(id='300227401823158288')
    conn, cur = database.get()

    while not bot.is_closed:
        msg = ''

        cur.execute(
            'SELECT * FROM Reminders WHERE finished = 0 AND targetedGroup LIKE \'everyone\' ORDER BY endTime DESC')
        reminders = cur.fetchall()

        if len(reminders) == 0:
            await bot.send_message(channel, 'No reminders at this time.')
            await asyncio.sleep(60)
            continue

        for r in reminders:
            msg += "Reminder by {}, finish by {}, reminder id {} : ".format(r[4], datetime.datetime.fromtimestamp(int(r[3])).strftime('%Y-%m-%d %H:%M:%S'), r[0])
            msg += r[1] + '\n'

        await bot.send_message(channel, msg)
        await bot.send_message(channel, '-' * 200)
        await asyncio.sleep(60)


async def targeted_announcement():
    conn, cur = database.get()
    await bot.wait_until_ready()

    while not bot.is_closed:
        cur.execute(
            'SELECT * FROM Reminders WHERE finished = 0')
        reminders = cur.fetchall()

        for r in reminders:
            targetGroup = r[6]
            if targetGroup != "everyone":
                user = await bot.get_user_info(targetGroup)
                msg = "Reminder by {}, finish by {}, reminder id {} : {}".format(r[4], datetime.datetime.fromtimestamp(int(r[3])).strftime('%Y-%m-%d %H:%M:%S'), r[0], r[1])
                await bot.send_message(user, msg)

        await asyncio.sleep(60)

# !registerRole <role>
@bot.command(pass_context=True)
async def registerRole(ctx, role: str):
    conn, cur = database.get()

    with conn:
        conn.execute("DELETE FROM Roles WHERE discordId=?", (ctx.message.author.id,))
        conn.execute("INSERT INTO Roles ('discordID', 'discordName', 'role') VALUES (?, ?, ?)",
                     (ctx.message.author.id, str(ctx.message.author).split('#')[0], role))

    await bot.say("Role {} registered.".format(role))


@bot.command(pass_context=True)
async def who(ctx, name: str):
    conn, cur = database.get()

    with conn:
        cur.execute(
            'SELECT * FROM Roles WHERE discordName LIKE \'{}\''.format(name))
        for r in cur:
            await bot.say("{} is a {}.".format(r[1], r[2]))


@bot.event
async def on_message(message):
    banned_words = ['sugar', 'coffee']
    if any(word in message.content for word in banned_words):
        await bot.send_message(message.channel, "Your({}) message contains a banned word. You have been muted for 10 seconds.".format(message.author))
        bot.server_voice_state(message.author, mute=True, deafen=True)
        await asyncio.sleep(10)
        bot.server_voice_state(message.author, mute=False, deafen=False)

    if message.content.startswith('!addReminder '):
        await addReminder(message)
        return

    if message.content.startswith('!createGist '):
        await createGist(message)
        return

    await bot.process_commands(message)


@bot.command()
async def createProject(name : str):
    conn, cur = database.get()

    r = gh.create_repository(name)
    if r:
        print(dir(r))
        await bot.say("Created {} successfully. Link: {}".format(r.name, r.clone_url))
    else:
        await bot.say("Github repo failed to create.")
        return

    with conn:
        conn.execute("INSERT INTO Projects ('name', 'repo') VALUES (?, ?)",
             (name, r.clone_url))


@bot.command()
async def requestProject(projectName : str):
    conn, cur = database.get()

    cur.execute("SELECT * FROM Projects WHERE name LIKE '{}'".format(projectName))
    projects = cur.fetchall()
    print(projects)

    for r in projects:
        await bot.say("GitHub Repo for project " + r[0] + "  :" + r[1])


@bot.command()
async def listProjects():
    conn, cur = database.get()


    cur.execute("SELECT * FROM Projects")
    projects = cur.fetchall()

    for p in projects:
        await bot.say("Project: {}, Finished {}, Link: {}".format(p[0], str(bool(p[2])), p[1]))


@bot.command()
async def finishProject(name: str):
    conn, cur = database.get()

    with conn:
        cur.execute(
            'UPDATE Projects set finished = 1 WHERE name LIKE \'{}\''.format(name))

    await bot.say("Successfully set project {} as finished.".format(name))


def helpString():
    msg = ''
    msg = msg + "!createProject <name> : creates project and sets up a GitHub repo\n\n" +\
                "!finishProject <name> : labels the project as finished\n\n" +\
                "!requestProject <name> : requests project by name and displays info\n\n" +\
                "!listProjects : lists all projects currently being developed and info\n\n" +\
                "!registerRole <role> : register project memember and assign role\n\n" +\
                "!addReminder <group> <endTimeDate>(dd/mm/yr/00:00) <message> : adds a reminder to list\n\n" +\
                "!listReminders : lists all reminders in the reminder list\n\n" +\
                "!finishReminder <reminderId>\n\n" +\
                "!commands : shows list of available bot commands\n\n" +\
                "!who <userName> : shows the role for that user\n\n" +\
                "!gistCreate <gistName> <contents> : creates a gist\n\n" +\
                "!listGists : lists gists\n\n" +\
                "!listReminders : lists reminders"

    return msg

@bot.command()
async def commands():
    await bot.say(helpString())


#!createGist <gistName> <contents>
async def createGist(message):
    conn, cur = database.get()

    tokens = message.content.split(' ')
    gistName = tokens[1]
    contents = ' '.join(tokens[2:])

    files = {
        '{}.txt'.format(gistName): {
            'content': contents
        }
    }

    gist = gh.create_gist(gistName, files)
    await bot.send_message(message.channel, "Gist created {}".format(gist.html_url))

    with conn:
        conn.execute("INSERT INTO Gists ('link', 'gistName') VALUES (?, ?)", (gist.html_url, gistName))


@bot.command()
async def listGists():
    conn, cur = database.get()

    cur.execute('SELECT * FROM Gists')
    gists = cur.fetchall()

    for g in gists:
        await bot.say("Name : {}\n Link: {}\n".format(g[1], g[0]))


@bot.command()
async def listReminders():
    conn, cur = database.get()

    msg = ''

    cur.execute(
        'SELECT * FROM Reminders WHERE finished = 0 AND targetedGroup LIKE \'everyone\' ORDER BY endTime DESC')
    reminders = cur.fetchall()

    if len(reminders) == 0:
        await bot.say('No reminders at this time.')

    for r in reminders:
        msg += "Reminder by {}, finish by {}, reminder id {} : ".format(r[4], datetime.datetime.fromtimestamp(
            int(r[3])).strftime('%Y-%m-%d %H:%M:%S'), r[0])
        msg += r[1] + '\n'

    await bot.say(msg)

@bot.event
async def on_member_join(member):
    bot.send_message(member, helpString())

bot.loop.create_task(announcement())
bot.loop.create_task(targeted_announcement())
bot.run(info.BOT_TOKEN)