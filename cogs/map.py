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
        mapping = "\n".join("".join(str(randint(0, n)) for _ in range(xsize)) for _ in range(ysize))
        return mapping

    def create_map(self, xsize, ysize, generators, spawners):
        return Map(self.generate_map(xsize=xsize, ysize=ysize, randoms=generators), generators, spawners,
                   [xsize // 2, ysize // 2], xsize, ysize)

    @commands.group(invoke_without_command=True, aliases=["carte"])
    @checks.no_pm()
    async def map(self, ctx, name: str):
        """See the server map"""
        map = await self.bot.di.get_map(ctx.guild, name)
        if map is None:
            await ctx.send("This server has no map!")
            return

        await ctx.send(f"{map.tiles}\n" + "\n".join(f"{i}: {item}" for i, item in enumerate(map.generators)))

    # Character meta has a "maps" key possibly, that will contain coords
    # "maps": {"Default": (0,0), "Moon": (32, 16)}

    @commands.command()
    @checks.no_pm()
    async def create(self, ctx, mapname: str, xmax: int, ymax: int):
        await ctx.send("What available tiles will there be? Say `done` when done. Use the * tile to describe all tiles "
                       "when adding what will spawn. One at a time send the name of the tile. i.e. grassland")
        maps = await self.bot.di.get_maps(ctx.guild)
        if len(maps) >= 5:
            await ctx.send("You can not have more than 5 maps! (For now)")
        generators = []
        spawners = {}

        check = lambda x: x.channel.id == ctx.channel.id and x.author.id == ctx.author.id
        while True:
            await ctx.send("What kind of tile is it? Say `done` when done")
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            tile = msg.content.strip()
            if tile == "done":
                break
            elif tile != "*":
                generators.append(tile)
            await ctx.send(
                "What things might spawn in those tiles? Split terms with commas. (Equal chance of each, repeat a term "
                "for greater chance)"
            )
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            if msg.content == "skip":
                continue
            spawners[tile] = Counter(msg.content.split(","))

        stile = [str(randint(0, len(generators) - 1))]
        new_map = Map(stile, generators, spawners, [0, 0], xmax, ymax)
        await self.bot.di.set_map(ctx.guild, mapname, new_map)
        await ctx.send(f"Map created with name {mapname}")

    '''
    @map.command(aliases=["look", "regarder", "inspect", "voir"])
    @checks.no_pm()
    async def check(self, ctx, mapname: str, character: str):
        """See what is on the current character's tile"""
        map = await self.bot.di.get_map(ctx.guild)
        if map is None:
            await ctx.send("This server has no map!")
            return

        chr = await self.bot.di.get_character(ctx.guild, character)
        if chr is None:
            await ctx.send("That character does not exist!")
        chmaps = chr.meta.get("maps")
        if not chmaps:
            xc = yc = 0
        else:
            if mapname in chmaps:
                xc, yc = chmaps[mapname]
            else:
                xc = yc = 0

        tiles = map.tiles.split("\n")
        xm, ym = len(tiles[0]), len(tiles)
        if None in (xc, yc) or xc > xm or yc > ym:
            xc, yc = ym // 2, ym // 2

        tile = map.generators[int(tiles[yc - 1][xc - 1])]
        spawners = map.spawners.get(tile)
        spawned = choices(*zip(*spawners.items()))

        await ctx.send(f"You are on a {tile} tile. There is {spawned}")
    '''

    @checks.admin_or_permissions()
    @map.command(aliases=["creer", "new", "nouvelle"])
    @checks.no_pm()
    async def generate(self, ctx, name: str, xsize: int, ysize: int):
        """Create a custom map for the guild.
        Usage: `rp!map create passive Earth 64 64`
            This will create a 64x64 map that will generate as the players explore it"""

        await ctx.send("What available tiles will there be? Say `done` when done. Use the * tile to describe all tiles "
                       "when adding what will spawn. One at a time send the name of the tile. i.e. grassland")
        maps = await self.bot.di.get_maps(ctx.guild)
        if len(maps) >= 5:
            await ctx.send("You can not have more than 5 maps! (For now)")
        generators = []
        spawners = {}

        check = lambda x: x.channel.id == ctx.channel.id and x.author.id == ctx.author.id
        while True:
            await ctx.send("What kind of tile is it? Say `done` when done")
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            tile = msg.content.strip()
            if tile == "done":
                break
            elif tile != "*":
                generators.append(tile)
            await ctx.send(
                "What things might spawn in those tiles? Split terms with commas. (Equal chance of each, repeat a term "
                "for greater chance)"
            )
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            if msg.content == "skip":
                continue
            spawners[tile] = Counter(msg.content.split(","))

        new_map = self.create_map(xsize, ysize, generators, spawners)
        await self.bot.di.set_map(ctx.guild, name, new_map)
        await ctx.send("Map created! View with rp!map")

    @map.command(aliases=["supprimer"])
    @checks.no_pm()
    @checks.admin_or_permissions()
    async def delete(self, ctx, name: str):
        await self.bot.di.set_map(ctx.guild, name, None)
        await ctx.send(f"Map {name} successfully deleted.")

    @map.command()
    @checks.no_pm()
    async def up(self, ctx, mapname, character):
        mapo = await self.bot.di.get_map(ctx.guild, mapname)
        char = await self.bot.di.get_char(ctx.guild, character)
        if char.owner != ctx.author.id:
            await ctx.send("You do not own this character!")
            return
        if mapo is None:
            await ctx.send("This map does not exist!")
            return

        spawn = mapo.spawn
        if not char.meta.get("maps"):
            char.meta["maps"] = {}
        if not char.meta["maps"].get(mapname):
            char.meta["maps"] = [0, 0]
        pos = char.meta["maps"][mapname]
        y = spawn[1] + pos[1]
        x = spawn[0] + pos[0]

        if y == 0:
            if len(mapo.tiles) >= mapo.maxy:
                print("You can't move any further this direction, you've hit the border")
                return
            else:
                spawn[1] += 1
                fh = "?" * x + self.rtile(mapo)
                lh = "?" * (len(mapo.tiles[0]) - len(fh) - 1)
                mapo.tiles.insert(0, fh + lh)

        pos[1] -= 1
        changed, spawned, tile = self.explore(mapo, x, y)
        if changed:
            await self.bot.di.set_map(ctx.guild, mapo)
        await self.bot.di.add_character(ctx.guild, char)

        await ctx.send(f"You enter a {mapo.generators[int(tile)]}. You see {spawned}")

    @map.command()
    @checks.no_pm()
    async def down(self, ctx, mapname: str, character: str):
        mapo = await self.bot.di.get_map(ctx.guild, mapname)
        char = await self.bot.di.get_char(ctx.guild, character)
        if char.owner != ctx.author.id:
            await ctx.send("You do not own this character!")
            return
        if mapo is None:
            await ctx.send("This map does not exist!")
            return

        spawn = mapo.spawn
        if not char.meta.get("maps"):
            char.meta["maps"] = {}
        if not char.meta["maps"].get(mapname):
            char.meta["maps"] = [0, 0]
        pos = char.meta["maps"][mapname]
        y = spawn[1] + pos[1]
        x = spawn[0] + pos[0]

        if y == (len(mapo.tiles) - 1):
            if len(mapo.tiles) >= mapo.maxy:
                print("You can't move any further this direction, you've hit the border")
                return
            else:
                fh = "?" * (x - 1) + self.rtile(mapo)
                lh = "?" * (len(mapo.tiles[0]) - len(fh))
                mapo.tiles.append(fh + lh)

        pos[1] += 1
        changed, spawned, tile = self.explore(mapo, x, y)
        if changed:
            await self.bot.di.set_map(ctx.guild, mapo)
        await self.bot.di.add_character(ctx.guild, char)

        await ctx.send(f"You enter a {mapo.generators[int(tile)]}. You see {spawned}")

    @map.command()
    @checks.no_pm()
    async def left(self, ctx, mapname: str, character: str):
        mapo = await self.bot.di.get_map(ctx.guild, mapname)
        char = await self.bot.di.get_char(ctx.guild, character)
        if char.owner != ctx.author.id:
            await ctx.send("You do not own this character!")
            return
        if mapo is None:
            await ctx.send("This map does not exist!")
            return

        spawn = mapo.spawn
        if not char.meta.get("maps"):
            char.meta["maps"] = {}
        if not char.meta["maps"].get(mapname):
            char.meta["maps"] = [0, 0]
        pos = char.meta["maps"][mapname]
        y = spawn[1] + pos[1]
        x = spawn[0] + pos[0]

        if x == 0:
            if len(mapo.tiles[0]) >= mapo.maxx:
                print("You can't move any further this direction, you've hit the border")
                return
            else:
                spawn[0] += 1
                for i in range(len(mapo.tiles)):
                    if i == y:
                        mapo.tiles[i] = self.rtile(mapo) + mapo.tiles[i]
                    else:
                        mapo.tiles[i] = "?" + mapo.tiles[i]

        pos[0] -= 1
        changed, spawned, tile = self.explore(mapo, x, y)
        if changed:
            await self.bot.di.set_map(ctx.guild, mapo)
        await self.bot.di.add_character(ctx.guild, char)

        await ctx.send(f"You enter a {mapo.generators[int(tile)]}. You see {spawned}")

    @map.command()
    @checks.no_pm()
    async def right(self, ctx, mapname: str, character: str):
        mapo = await self.bot.di.get_map(ctx.guild, mapname)
        char = await self.bot.di.get_char(ctx.guild, character)
        if char.owner != ctx.author.id:
            await ctx.send("You do not own this character!")
            return
        if mapo is None:
            await ctx.send("This map does not exist!")
            return

        spawn = mapo.spawn
        if not char.meta.get("maps"):
            char.meta["maps"] = {}
        if not char.meta["maps"].get(mapname):
            char.meta["maps"] = [0, 0]
        pos = char.meta["maps"][mapname]
        y = spawn[1] + pos[1]
        x = spawn[0] + pos[0]

        if x == (len(mapo.tiles[0]) - 1):
            if len(mapo.tiles[0]) >= mapo.maxx:
                print("You can't move any further this direction, you've hit the border")
                return
            else:
                for i in range(len(mapo.tiles)):
                    if i == y:
                        mapo.tiles[i] += self.rtile(mapo)
                    else:
                        mapo.tiles[i] += "?"

        pos[0] += 1
        changed, spawned, tile = self.explore(mapo, x, y)
        if changed:
            await self.bot.di.set_map(ctx.guild, mapo)
        await self.bot.di.add_character(ctx.guild, char)

        await ctx.send(f"You enter a {mapo.generators[int(tile)]}. You see {spawned}")

    def explore(self, mapo: Map, x: int, y: int):
        tile = mapo.tiles[x][y]
        changed = False
        if tile == "?":
            changed = True
            f = list(mapo.tiles[x])
            f[x] = self.rtile(mapo)
            mapo.tiles[y] = "".join(f)
            tile = f[x]

        spawnable = mapo.spawners.get(int(tile))
        if not spawnable:
            spawnable = mapo.spawners.get(-1)

        if not spawnable:
            spawned = "nothing"
        else:
            spawned = choices(*zip(*spawnable.items()))[0]
            if spawned is None:
                spawned = "nothing"

        return changed, spawned, tile

    @map.command(aliases=["look", "regarder", "inspect", "voir"])
    @checks.no_pm()
    async def check(self, ctx, mapname: str, character: str):
        mapo = await self.bot.di.get_map(ctx.guild, mapname)
        char = await self.bot.di.get_char(ctx.guild, character)
        if char.owner != ctx.author.id:
            await ctx.send("You do not own this character!")
            return
        if mapo is None:
            await ctx.send("This map does not exist!")
            return

        spawn = mapo.spawn
        if not char.meta.get("maps"):
            char.meta["maps"] = {}
        if not char.meta["maps"].get(mapname):
            char.meta["maps"] = [0, 0]
        pos = char.meta["maps"][mapname]
        y = spawn[1] + pos[1]
        x = spawn[0] + pos[0]

        surrounding = self.ndslice(mapo.tiles, (y - 1, y + 2), (x - 1, x + 2))
        await ctx.send("\n".join(surrounding))
        await ctx.send("\n".join(f"{i}: {item}" for i, item in enumerate(mapo.generators)))

    def rtile(self, mapo):
        return str(randint(0, len(mapo.generators) - 1))

    def ndslice(self, l, ysl, xsl):
        return [e[slice(*ysl)] for e in l[slice(*xsl)]]
