from discord.ext import commands
import discord
from .utils import checks

containers = dict()


class Containers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.command(aliases=["bag", "pocket"])
    async def containers(self, ctx):
        pass

    @containers.command()
    async def create(self, type, capacity=None):
        """Lets you create a container in which to put items, optionally you can put in a maximum capacity to
        Limit the amount of items with the \"weight\" attribute that can fit"""
        pass

    @containers.command()
    async def open(self, container):
        """Open a container to see whats inside!"""
        pass

    @containers.command()
    async def delete(self, container):
        """Delete an existing container"""
        pass
