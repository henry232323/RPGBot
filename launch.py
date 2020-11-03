import subprocess as sp

from discord.ext import commands

bot = commands.Bot(command_prefix="!")

process = None  # sp.Popen(['python3', 'main.py'])
authorized_users = [125660719323676672, 141211057485119488, 122739797646245899]


def is_authorized(ctx):
    def predicate():
        return ctx.author.id in authorized_users

    return predicate


@bot.event
async def on_ready():
    global process
    print("Launcher Ready")

    if process is None:
        process = sp.Popen(['python3.8', 'main.py'])


@bot.command()
@commands.check(is_authorized)
async def rstart(ctx):
    """Starts the Bot"""
    global process
    if process is not None and process.poll() is None:
        await ctx.channel.send('It\'s already running!')
        return
    process = sp.Popen(['python3.8', 'main.py'])
    await ctx.channel.send("Starting!")


@bot.command()
@commands.check(is_authorized)
async def rstatus(ctx):
    """Displays Bot Status"""
    result = process.poll()
    if not result:
        await ctx.send("Still running")
        return
    await ctx.send(result)
    out, err = process.communicate()
    await ctx.send(out or "No out")
    await ctx.send(err or "No err")


@bot.command()
@commands.check(is_authorized)
async def rterminate(ctx):
    """Terminates the Bot"""
    process.terminate()
    process.wait()
    await ctx.channel.send("Terminated!")


@bot.command()
@commands.check(is_authorized)
async def rrestart(ctx):
    await rterminate(ctx)
    await rstart(ctx)


@bot.command()
@commands.check(is_authorized)
async def rupdate(ctx):
    """Updates the Bot"""
    sp.run(['git', 'fetch', '--all'])
    sp.run(['git', 'reset', '--hard', 'origin/master'])
    sp.run(['git', 'pull'])
    await ctx.send("Update Complete")


@bot.command()
@commands.check(is_authorized)
async def rupdog(ctx):
    sp.run(['git', 'fetch', '--all'])
    sp.run(['git', 'reset', '--hard', 'origin/master'])
    sp.run(['git', 'pull'])
    await rterminate(ctx)
    await rstart(ctx)
    await ctx.send("Updog Complete")


bot.run(open("resources/beta_auth").read())
