from discord.ext import commands
import discord
from .utils import checks

containers = dict()

class Containers:
    @commands.command()
    @checks.no_pm()
    async def create(self, type):
        pass
