from random import randint, choices
from collections import Counter
from discord.ext import commands

from .utils.data import Map
from .utils import checks


class Mapping:
    def __init__(self, bot):
        """Server map utilities"""
        self.bot = bot

    def generate_map(self, *, xsize: int, ysize: int, randoms: list):
        if xsize > 64 or ysize > 64 or xsize < 2 or ysize < 2:
            raise ValueError("x or y cannot exceed 64 and must be at least 2!")
        n = len(randoms) - 1
        mapping = "\n".join("".join(randint(0, n) for _ in range(xsize)) for _ in range(ysize))
        return mapping

    def create_map(self, xsize, ysize, generators, spawners):
        return Map(self.generate_map(xsize=xsize, ysize=ysize, randoms=generators), generators, spawners)

    @commands.group(invoke_without_command=True, aliases=["carte"])
    @checks.no_pm()
    async def map(self, ctx):
        """See the server map"""
        map = await self.bot.di.get_map(ctx.guild)
        if map is None:
            await ctx.send("This server has no map!")
            return

        await ctx.send(f"{map.tiles}\n" + "\n".join(f"{i}: {item}" for i, item in enumerate(map.generators)))

    @map.command(aliases=["look", "regarder", "inspect", "voir"])
    @checks.no_pm()
    async def check(self, ctx, character: str):
        """See what is on the current character's tile"""
        map = await self.bot.di.get_map(ctx.guild)
        if map is None:
            await ctx.send("This server has no map!")
            return

        chr = await self.bot.di.get_character(ctx.guild, character)
        if chr is None:
            await ctx.send("That character does not exist!")
        xc, yc = chr.meta.get("x"), chr.meta.get("y")
        tiles = map.tiles.split("\n")
        xm, ym = len(tiles[0]), len(tiles)
        if None in (xc, yc) or xc > xm or yc > ym:
            xc, yc = ym // 2, ym // 2

        tile = map.generators[tiles[yc - 1][xc - 1]]
        spawners = map.spawners.get(tile)
        spawned = choices(*zip(*spawners.items()))

        await ctx.send(f"You are on a {tile} tile. There is {spawned}")

    @map.command(aliases=["creer", "new", "nouvelle"])
    @checks.no_pm()
    async def create(self, ctx, xsize: int, ysize: int):
        """Create a custom map for the guild (if one exists it will be overwritten)"""
        await ctx.send("What available tiles will there be? Say `done` when done. Use the * tile to describe all tiles "
                       "when adding what will spawn.")
        generators = []
        spawners = {}

        check = lambda x: x.channel.id == ctx.channel.id and x.author.id == ctx.author.id
        while True:
            msg = await self.bot.wait_for("message", check, timeout=60)
            tile = msg.content
            if tile == "done":
                break
            elif tile != "*":
                generators.append(tile)
            await ctx.send(
                "What things might spawn in those tiles? Split terms with commas. (Equal chance of each, repeat a term "
                "for greater chance)"
            )
            msg = await self.bot.wait_for("message", check, timeout=60)
            if msg.content == "skip":
                continue
            spawners[tile] = Counter(msg.split(","))

        new_map = self.create_map(xsize, ysize, generators, spawners)
        await self.bot.di.set_map(ctx.guild, new_map)
        await ctx.send("Map created! View with rp!map")

    @map.command(aliases=["bouger", "aller", "go"])
    @checks.no_pm()
    async def move(self, character: str, direction: str):
        """Move a character in a direction (valid directions include N/S/E/W for the cardinal directions respectively)"""
