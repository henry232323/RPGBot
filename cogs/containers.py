from discord.ext import commands
import discord
from .utils import checks

containers = dict()

class Containers:
    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))


    @commands.command()
    async def create(self, type):
        pass