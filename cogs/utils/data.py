#!/usr/bin/env python3
# Copyright (c) 2016-2017, henry232323
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import discord
from discord.ext import commands
from recordclass import recordclass as namedtuple
import ujson as json
from async_timeout import timeout

from collections import Counter
import re
import asyncio
from random import randint

from .translation import _
from builtins import property as _property, tuple as _tuple
from operator import itemgetter as _itemgetter
from collections import OrderedDict

Pet = namedtuple("Pet", ["id", "name", "type", "stats", "meta"])
ServerItem = namedtuple("ServerItem", ["name", "description", "meta"])
# Character = namedtuple("Character", ["name", "owner", "description", "level", "team", "meta"])

gc = namedtuple("Guild",
                ["name", "owner", "description", "members", "bank", "items", "open", "image", "icon", "invites",
                 "mods"])
Map = namedtuple("Map", ["tiles", "generators", "spawners", "spawn", "maxx", "maxy"])
AdvancedMap = namedtuple("AdvancedMap", ["tiles", "generators", "spawners", "spawnables", "spawn", "type"])


class ContextManagerLockWrapper:
    def __init__(self, manager, resource):
        self.manager = manager
        self.resource = resource

    async def __aenter__(self):
        try:
            async with timeout(10 * 60):
                await self.manager.acquire(self.resource)
        except asyncio.TimeoutError:
            self.manager.release(self.resource)
            await self.manager.bot.get_user(self.manager.bot.owner_id)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.manager.release(self.resource)


class ResourceManager:
    def __init__(self, bot, lock_factory=asyncio.Lock):
        """A class for managing multiple locks on arbitrary resources."""
        self.locks = {}
        self._lock_factory = lock_factory
        self.bot = bot

    async def acquire(self, resource):
        if resource in self.locks:
            await self.locks[resource].acquire()
        else:
            lock = self.locks[resource] = self._lock_factory()
            await lock.acquire()

    def release(self, resource):
        if resource in self.locks:
            lock = self.locks[resource]
            lock.release()
            if not lock.locked():
                del self.locks[resource]
        else:
            raise RuntimeError("This lock is not being held!")

    def lock(self, resource):
        return ContextManagerLockWrapper(self, resource)


class Character(tuple):
    """Character(name, owner, description, level, team, meta)"""
    __slots__ = ()
    _fields = ('name', 'owner', 'description', 'level', 'team', 'meta', 'ustats')

    def __new__(_cls, name, owner, description, level, team, meta, ustats=None):
        'Create new instance of Character(name, owner, description, level, team, meta)'
        if ustats is None:
            ustats = {}
        return _tuple.__new__(_cls, (name, owner, description, level, team, meta, ustats))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        """Make a new Character object from a sequence or iterable"""
        result = new(cls, iterable)
        if len(result) != 6:
            raise TypeError('Expected 6 arguments, got %d' % len(result))
        return result

    def _replace(_self, **kwds):
        """Return a new Character object replacing specified fields with new values"""
        result = _self._make(map(kwds.pop, ('name', 'owner', 'description', 'level', 'team', 'meta'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % list(kwds))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + '(name=%r, owner=%r, description=%r, level=%r, team=%r, meta=%r, ustats=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values.'
        return OrderedDict(zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    name = _property(_itemgetter(0), doc='Alias for field number 0')
    owner = _property(_itemgetter(1), doc='Alias for field number 1')
    description = _property(_itemgetter(2), doc='Alias for field number 2')
    level = _property(_itemgetter(3), doc='Alias for field number 3')
    team = _property(_itemgetter(4), doc='Alias for field number 4')
    meta = _property(_itemgetter(5), doc='Alias for field number 5')
    ustats = _property(_itemgetter(6), doc='Alias for field number 6')


converters = {
    discord.Member: commands.MemberConverter,
    discord.User: commands.UserConverter,
    discord.TextChannel: commands.TextChannelConverter,
    discord.VoiceChannel: commands.VoiceChannelConverter,
    discord.Invite: commands.InviteConverter,
    discord.Role: commands.RoleConverter,
    discord.Game: commands.GameConverter,
    discord.Colour: commands.ColourConverter
}


def parse_varargs(s):
    view = commands.view.StringView(s)
    end = []
    while True:
        view.skip_ws()
        next = view.get_quoted_word()
        if next is None:
            break
        end.append(next.strip())
    return end


def chain(l):
    for item in l:
        try:
            itr = iter(item)
            for ytem in itr:
                yield ytem
        except:
            yield item


class Guild(gc):
    __slots__ = ()

    def __new__(cls, name, owner, description="", members=None, bank=0, items=None, open=False, image=None, icon=None,
                invites=None, mods=None):
        if members is None:
            members = set()
        if items is None:
            items = dict()
        if invites is None:
            invites = set()
        if mods is None:
            mods = set()
        return super().__new__(cls, name, owner, description, members, bank, items, open, image, icon, invites, mods)


class MemberConverter(commands.MemberConverter):
    async def convert(self, ctx, argument):
        if argument == 'everyone' or argument == '@everyone':
            return ctx.guild.members
        try:
            role = await commands.RoleConverter.convert(self, ctx, argument)
            return role.members
        except:
            return await super().convert(ctx, argument)


class NumberConverter(commands.Converter):
    async def convert(self, ctx, argument):
        argument = argument.replace(",", "").strip("$")
        if not argument.strip("-").replace(".", "").isdigit():
            raise commands.BadArgument("That is not a number!")
        if len(argument) > 10:
            raise commands.BadArgument("That number is much too big! Must be less than 999,999,999")
        return round(float(argument), 2)


class IntConverter(commands.Converter):
    async def convert(self, ctx, argument):
        argument = argument.replace(",", "").strip("$")
        if not argument.strip("-").replace(".", "").isdigit():
            raise commands.BadArgument("That is not a number!")
        if len(argument) > 10:
            raise commands.BadArgument("That number is much too big! Must be less than 999,999,999")
        return int(argument)


class ItemOrNumber(commands.Converter):
    async def convert(self, ctx, argument):
        fargument = argument.replace(",", "").strip("$")
        if not fargument.strip("-").replace(".", "").isdigit():
            if "x" in argument:
                item, n = argument.split("x")
                if n.isdigit():
                    return item, int(n)
            return argument
        if len(fargument) > 10:
            raise commands.BadArgument("That number is much too big! Must be less than 999,999,999")
        return round(float(fargument), 2)


class Object:
    def __init__(self, d={}, **kwargs):
        for k, v in d.items():
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)


def union(*classes):
    class Union(commands.Converter):
        async def convert(self, ctx, argument):
            for cls in classes:
                try:
                    if cls in converters:
                        cls = converters[cls]
                    return await cls.convert(self, ctx, argument)
                except Exception as e:
                    pass
            else:
                raise e

    return Union


regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def validate_url(url):
    return bool(regex.fullmatch(url))


def get(iterable, **attrs):
    attr, val = list(attrs.items())[0]

    fin = [element for element in iterable if getattr(element, attr) in val]
    fin.sort(key=lambda x: val.index(getattr(x, attr)))

    if len(fin) < len(val):
        fin = []
        for x in val:
            fin.append(discord.utils.get(iterable, **{attr: x}))

    return None or fin


def chunkn(s, n=2000, splitter="\n"):
    s = s.split(splitter)
    chunks = [[]]
    ctr = 0
    ictr = 0
    for str in s:
        ctr += len(str) + 1
        if ctr > n:
            ictr += 1
            chunks.append([])

        chunks[ictr].append(str)

    return chunks


async def create_pages(ctx, items, lfmt,
                       description=None, title=None,
                       author=None, author_url=None,
                       emotes=("\u2B05", "\u27A1", "\u274C"),
                       thumbnail=None, footer=None, chunk=25):
    embed = discord.Embed(description=description, title=title, color=randint(0, 0xFFFFFF))
    embed.set_author(name=author, icon_url=author_url)
    if thumbnail:
        embed.set_thumbnail(
            url=thumbnail
        )
    if footer:
        embed.set_footer(text=footer)

    items = {k: lfmt(v) for k, v in items}
    ctr = 0
    counter = 0
    while any(len(v) > 500 for v in items.values()) and ctr < 20:
        additions = {}
        counter += 1
        for k, v in items.items():
            if len(v) > 750:
                count = 0
                start = ""
                end = ""
                for item in v.split("\n"):
                    if count + len(item) > 500:
                        end += item + "\n"
                    else:
                        start += item + "\n"
                        count += len(item) + 1
                additions[k] = start.strip()
                if end.strip():
                    additions[k[0] + " " + str(counter)] = end.strip()
        items.update(additions)
        ctr += 1
    i = 0
    ditems = items
    items = list(items.items())
    items.sort()

    chunks = []
    for j in range(0, len(items), chunk):
        chunks.append(items[j:j + chunk])

    for item, value in chunks[i]:
        embed.add_field(name=item, value=ditems[item].strip() or "None")

    end = len(chunks) - 1

    msg = await ctx.send(embed=embed)
    for emote in emotes:
        await msg.add_reaction(emote)

    while True:
        try:
            r, u = await ctx.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id, timeout=80)
        except asyncio.TimeoutError:
            await ctx.send(await _(ctx, "Timed out! Try again"))
            try:
                await msg.delete()
            except:
                pass
            return

        if u == ctx.guild.me:
            continue

        if u != ctx.author or r.emoji not in emotes:
            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass
            continue

        if r.emoji == emotes[0]:
            if i == 0:
                pass
            else:
                embed.clear_fields()
                i -= 1
                for item, value in chunks[i]:
                    embed.add_field(name=item, value=ditems[item].strip() or "None")

                await msg.edit(embed=embed)

        elif r.emoji == emotes[1]:
            if i == end:
                pass
            else:
                embed.clear_fields()
                i += 1
                for item, value in chunks[i]:
                    embed.add_field(name=item, value=ditems[item].strip() or "None")

                await msg.edit(embed=embed)
        else:
            try:
                await msg.delete()
            except:
                pass
            await ctx.send(await _(ctx, "Closing"))
            return

        try:
            await msg.remove_reaction(r.emoji, u)
        except:
            pass


default_user = {
    "money": 0,
    "box": [],
    "items": dict(),
    "guild": None,
    "level": 1,
    "exp": 0
}

default_server = {
    "start": 0,
    "items": dict(),
    "characters": dict(),
    "market_items": dict(),
    "loot_boxes": dict(),
    "guilds": dict(),
    "shop_items": dict(),
    "recipes": dict(),
    "prefix": ['rp!', 'pb!', '<@305177429612298242> ', 'Rp!'],
    "cmdprefixes": {},
}

example_pet = {
    "id": 0,
    "name": "Pichi",
    "type": "Pikachu",
    "stats": {
        "level": 15,
        "health": 22,
        "attack": 34,
        "defense": 15,
        "spatk": 46,
        "spdef": 29
    },
    "meta": {
        "color": "yellow",
        "nature": "hasty"
    }
}

example_serveritem = {
    "name": "pokeball",
    "description": "Used to catch Pet, one of the weakest balls",
    "meta": {
        "color": "red and white",
        "rate": 20
    }
}

example_character = {
    "name": "Ash Ketchum",
    "owner": 166349353999532035,
    "description": "Likes to catch pets",
    "level": 25,
    "team": [0],
    "meta": {
        "hair": "black",
        "favorite_pet": "Pichi",
        "image": "http://pa1.narvii.com/6320/3cf4ee1c3106552c4d8116218d556b97da0da020_128.gif"
    }
}

example_user = {
    "money": 25,
    "box": [
        Pet(**example_pet)
    ],
    "items": {
        "pokeball": 12
    }
}

example_server = {
    "start": 500,
    "items": {
        "pokeball": ServerItem(**example_serveritem)
    }
}

example_market = {
    "id": "ab782dgi"
}

example_guild = {
    "name": "Dank Memers",
    "owner": 166349353999532035,
    "description": "We meme dankely",
    "members": {166349353999532035},
    "bank": 5123890,
    "items": Counter(bananas=5),
    "open": False,
    "invites": {166349353999532035},
    "image": None,
    "icon": None,
    "mods": {166349353999532035}
}

example_map = {
    "tiles": "01233212313132312\n12312312381231231\n",
    "generators": ["grass", "desert", "dungeon"],
    "spawners": {
        "grass": {"dog": 1},
        "dungeon": {"swordsman": 12},
        "*": {
            "horse": 12,
            "cow": 3
        }
    }
}


class DataInteraction(object):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.rm = ResourceManager(bot)

    async def get_team(self, guild, character):
        gd = await self.db.get_guild_data(guild)
        character = Character(*gd["characters"][character])
        owner = discord.utils.get(guild.members, id=character.owner)
        ud = await self.db.get_user_data(owner)

        pet = [Pet(*x) for x in ud["box"] if x[0] in character.team]

        return pet

    async def get_box(self, member):
        """Get user's Pet box"""
        ub = await self.db.user_item(member, "box")
        return [Pet(*x) for x in json.loads(ub)]

    async def get_balance(self, member):
        """Get user's balance"""
        return float(await self.db.user_item(member, "money"))

    async def get_all_balances(self, member):
        ud = await self.db.get_user_data(member)
        bal = ud.get("money", 0)
        bank = ud.get("bank", 0)
        return (bal, bank)

    async def get_inventory(self, member):
        """Get user's inventory"""
        ui = await self.db.user_item(member, "items")
        return json.loads(ui) if ui else {}

    async def get_salary_ctime(self, member):
        """Get user's inventory"""
        ud = await self.db.get_user_data(member)
        return ud.get('ctimes', {})

    async def get_user_guild(self, member):
        """Get user's associated guild"""
        ud = await self.db.user_item(member, "guild")
        return ud

    async def get_user_level(self, member):
        """Get user's level"""
        ud = await self.db.get_user_data(member)
        return (ud.get("level", 1), ud.get("exp", 0))

    async def get_pet(self, member, id):
        """Get a user's Pet with the given ID"""
        box = await self.get_box(member)
        for x in box:
            if x[0] == id:
                return x
        else:
            raise KeyError("Pet doesn't exist!")

    async def get_guild_start(self, guild):
        """Get a Server's user starting balance"""
        return (await self.db.get_guild_data(guild)).get("start", 0)

    async def get_guild_recipes(self, guild):
        recipes = (await self.db.get_guild_data(guild)).get("recipes", {})
        return {a if isinstance(a, str) else " ".join(a): b for a, b in recipes.items()}

    async def get_guild_items(self, guild):
        """Get all the items available in a server"""
        gd = await self.db.get_guild_data(guild)
        return {y: ServerItem(*x) for y, x in gd["items"].items()}

    async def get_guild_lootboxes(self, guild):
        """Get a server's lootboxes"""
        gd = await self.db.get_guild_data(guild)
        return gd.get("lootboxes", dict())

    async def get_guild_market(self, guild):
        """Get the current market of a server"""
        gd = await self.db.get_guild_data(guild)
        return gd.get("market_items", dict())

    async def get_guild_shop(self, guild):
        """Get the current market of a server"""
        gd = await self.db.get_guild_data(guild)
        return gd.get("shop_items", dict())

    async def get_guild_characters(self, guild):
        """Get all the characters for a server"""
        gd = await self.db.get_guild_data(guild)
        return {y: Character(*x) for y, x in gd["characters"].items()}

    async def get_character(self, guild, name):
        data = await self.db.get_guild_data(guild)
        chrs = {y: Character(*x) for y, x in data["characters"].items()}
        if "caliases" not in data:
            data["caliases"] = {}
        if name in data["caliases"]:
            name = data["caliases"][name]
        return chrs.get(name)

    async def get_map(self, guild, name):
        gd = await self.db.get_guild_data(guild)
        maps = gd.get("maps", {})
        if isinstance(maps, Map):
            maps = {"Default": maps}
        map = maps.get(name)
        if not map:
            return
        if isinstance(map[3], dict):
            return AdvancedMap(*map)
        return Map(*map)

    async def get_maps(self, guild):
        gd = await self.db.get_guild_data(guild)
        maps = gd.get("maps", {})
        if isinstance(maps, Map):
            maps = {"Default": maps}
        return {name: Map(*map) if not isinstance(map[3], dict) else AdvancedMap(*map) for name, map in maps.items()}

    async def get_language(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("lang", {})

    async def get_exp_enabled(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("exp", True)

    async def get_salaries(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("salaries", {})

    async def get_currency(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("currency", "$")

    async def get_delete_time(self, guild):
        gd = await self.db.get_guild_data(guild)
        t = gd.get("msgdel", None)
        return t if t is not 0 else None

    async def get_guild_guilds(self, guild):
        """Get a server's guilds"""
        gd = await self.db.get_guild_data(guild)
        gobj = {y: Guild(*x) for y, x in gd.get("guilds", dict()).items()}
        return gobj

    async def add_pet(self, owner, pet):
        """Create a Pet for a user's box"""
        ud = await self.db.get_user_data(owner)
        if isinstance(pet, dict):
            if not 'id' in pet:
                id = ud["box"][-1][0] + 1 if ud["box"] else 0
                ud["box"].append(Pet(**pet, id=id))
            else:
                id = pet['id']
                ud["box"].append(Pet(**pet))
        else:
            id = pet.id
            for i, npet in enumerate(ud["box"]):
                if npet[0] == id:
                    ud["box"][i] = pet
        await self.db.update_user_data(owner, ud)
        return id

    async def remove_pet(self, owner, id):
        """Remove a Pet from a user's box"""
        ud = await self.db.get_user_data(owner)
        for x in ud["box"]:
            if x[0] == id:
                break
        else:
            raise ValueError("This is not a valid ID!")
        ud["box"].remove(x)
        await self.db.update_user_data(owner, ud)
        return Pet(*x)

    async def new_item(self, guild, serveritem):
        """Create a new server item"""
        gd = await self.db.get_guild_data(guild)
        gd["items"][serveritem.name] = serveritem
        await self.db.update_guild_data(guild, gd)

    async def new_items(self, guild, serveritems):
        """Create a new server item"""
        gd = await self.db.get_guild_data(guild)
        for item in serveritems:
            gd["items"][item.name] = item
        await self.db.update_guild_data(guild, gd)

    async def update_guild_items(self, guild, serveritems):
        """Create a new server item"""
        gd = await self.db.get_guild_data(guild)
        gd["items"] = dict()
        for item in serveritems:
            gd["items"][item.name] = item
        await self.db.update_guild_data(guild, gd)

    async def remove_item(self, guild, item):
        """Remove a server item"""
        gd = await self.db.get_guild_data(guild)
        del gd["items"][item]
        await self.db.update_guild_data(guild, gd)

    async def remove_items(self, guild, *items):
        """Remove a server item"""
        gd = await self.db.get_guild_data(guild)
        for item in items:
            gd["items"].pop(item, None)
        await self.db.update_guild_data(guild, gd)

    async def add_character(self, guild, character):
        """Add a new character to a guild"""
        gd = await self.db.get_guild_data(guild)
        gd["characters"][character.name] = character
        await self.db.update_guild_data(guild, gd)

    async def remove_character(self, guild, name):
        """Remove a character from a guild"""
        gd = await self.db.get_guild_data(guild)
        del gd["characters"][name]
        await self.db.update_guild_data(guild, gd)

    async def give_items(self, member, *items):
        """Give a user items"""
        ud = await self.db.get_user_data(member)
        ud["items"] = Counter(ud["items"])
        ud["items"].update(dict(items))
        await self.db.update_user_data(member, ud)
        return ud["items"]

    async def take_items(self, member, *items):
        """Take items from a user"""
        ud = await self.db.get_user_data(member)
        ud["items"] = Counter(ud["items"])
        ud["items"].subtract(dict(items))

        for item, value in list(ud["items"].items()):
            if value < 0:
                raise ValueError("Cannot take more items than the user has!")
            if value == 0:
                del ud["items"][item]

        await self.db.update_user_data(member, ud)
        return ud["items"]

    async def take_items_override(self, member, *items):
        """Take items from a user (set to zero instead of error)"""
        ud = await self.db.get_user_data(member)
        ud["items"] = Counter(ud["items"])
        ud["items"].subtract(dict(items))

        for item, value in list(ud["items"].items()):
            if value <= 0:
                del ud["items"][item]

        await self.db.update_user_data(member, ud)
        return ud["items"]

    async def update_items(self, member, *items):
        """Take items from a user"""
        ud = await self.db.get_user_data(member)
        ud["items"] = Counter(ud["items"])
        ud["items"].update(dict(items))

        for item, value in list(ud["items"].items()):
            if value <= 0:
                del ud["items"][item]

        await self.db.update_user_data(member, ud)
        return ud["items"]

    async def add_eco(self, member, amount):
        """Give (or take) a user('s) money"""
        ud = await self.db.get_user_data(member)
        if ud["money"] + amount < 0 and (ud["money"] >= 0 or amount < 0):
            raise ValueError("Cannot take more than user has!")
        ud["money"] += amount
        await self.db.update_user_data(member, ud)
        return ud["money"]

    async def take_from_bank(self, member, amount):
        """Take a user('s) money, draining from the bank if necessary"""
        ud = await self.db.get_user_data(member)
        ud["money"] -= amount
        if "bank" not in ud:
            ud["bank"] = 0
        if ud["money"] < 0:
            ud["bank"] += ud["money"]
            if ud["bank"] < 0:
                raise ValueError("Cannot take more than user has!")
        await self.db.update_user_data(member, ud)
        return ud["money"], ud["bank"]

    async def set_salary_ctime(self, member, ctimes):
        """Give a user items"""
        ud = await self.db.get_user_data(member)
        ud["ctimes"] = ctimes
        await self.db.update_user_data(member, ud)

    async def update_salaries(self, guild, data):
        gd = await self.db.get_guild_data(guild)
        gd["salaries"] = data
        await self.db.update_guild_data(guild, gd)

    async def set_delete_time(self, guild, time):
        gd = await self.db.get_guild_data(guild)
        gd["msgdel"] = time
        await self.db.update_guild_data(guild, gd)

    async def set_language(self, guild, language):
        gd = await self.db.get_guild_data(guild)
        gd["lang"] = language
        await self.db.update_guild_data(guild, gd)

    async def set_default_map(self, guild, value):
        gd = await self.db.get_guild_data(guild)
        gd["default_map"] = value
        await self.db.update_guild_data(guild, gd)

    async def get_default_map(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("default_map")

    async def set_currency(self, guild, currency):
        if len(currency) > 30:
            raise ValueError("Currency prefix too long!")
        gd = await self.db.get_guild_data(guild)
        gd["currency"] = currency
        await self.db.update_guild_data(guild, gd)

    async def set_eco(self, member, amount):
        """Set a user's balance"""
        ud = await self.db.get_user_data(member)
        ud["money"] = amount
        ud["bank"] = 0
        await self.db.update_user_data(member, ud)
        return ud["money"]

    async def set_balances(self, member, bal=None, bank=None):
        """Set a user's balance and bank balance"""
        ud = await self.db.get_user_data(member)
        if bal is not None:
            ud["money"] = bal
        if bank is not None:
            ud["bank"] = bank
        await self.db.update_user_data(member, ud)

    async def set_start(self, guild, amount):
        """Set a server's user start balance"""
        gd = await self.db.get_guild_data(guild)
        gd["start"] = amount
        await self.db.update_guild_data(guild, gd)

    async def add_exp(self, member, exp):
        ud = await self.bot.db.get_user_data(member)
        if ud.get("level") is None:
            ud["level"] = 0
            ud["exp"] = 0
        s = ud["level"]
        ud["exp"] += exp
        next = self.bot.get_exp(ud["level"])
        while ud["exp"] > next:
            ud["level"] += 1
            ud["exp"] -= next
            next = self.bot.get_exp(ud["level"])

        await self.db.update_user_data(member, ud)
        return ud["level"] if ud["level"] > s else None

    async def set_exp_enabled(self, guild, value):
        gd = await self.db.get_guild_data(guild)
        gd["exp"] = value
        await self.db.update_guild_data(guild, gd)

    async def add_recipe(self, guild, name: str, itemsin: dict, itemsout: dict):
        gd = await self.db.get_guild_data(guild)
        if "recipes" not in gd:
            gd["recipes"] = {}
        recipes = gd["recipes"]
        recipes[name] = (itemsin, itemsout)
        await self.db.update_guild_data(guild, gd)

    async def remove_recipe(self, guild, name):
        gd = await self.db.get_guild_data(guild)
        del gd.get("recipes", {})[name]
        await self.db.update_guild_data(guild, gd)

    async def add_to_team(self, guild, character, id):
        """Add a pet to a character's team"""
        gd = await self.db.get_guild_data(guild)
        character = gd["characters"][character]
        character[4].append(id)
        if len(character[4]) > 6:
            raise ValueError("Team is limited to 6!")
        await self.db.update_guild_data(guild, gd)

    async def set_guild(self, member, name):
        ud = await self.db.get_user_data(member)
        ud["guild"] = name
        await self.db.update_user_data(member, ud)

    async def set_map(self, guild, name, map):
        gd = await self.db.get_guild_data(guild)
        if "maps" not in gd:
            gd["maps"] = {}
        gd["maps"][name] = map
        return await self.db.update_guild_data(guild, gd)

    async def remove_map(self, guild, name):
        gd = await self.db.get_guild_data(guild)
        maps = gd.get("maps")
        if maps and name in maps:
            del gd["maps"][name]
        return await self.db.update_guild_data(guild, gd)

    async def set_pos(self, guild, map, character, pos):
        char = await self.get_character(guild, character)
        maps = char.meta.get("maps")
        if maps is None:
            char.meta["maps"] = {}
        char.meta["maps"][map] = pos
        await self.add_character(guild, character)

    async def set_level(self, member, level, exp):
        ud = await self.db.get_user_data(member)
        ud["level"] = level
        ud["exp"] = exp
        return await self.db.update_user_data(member, ud)

    async def remove_from_team(self, guild, character, id):
        """Remove a pet from a character's team"""
        gd = await self.db.get_guild_data(guild)
        character = gd[4][character]
        character[4].remove(id)
        await self.db.update_guild_data(guild, gd)

    async def update_guild_market(self, guild, data):
        """Update a server's market"""
        gd = await self.db.get_guild_data(guild)
        gd["market_items"] = data
        return await self.db.update_guild_data(guild, gd)

    async def update_guild_lootboxes(self, guild, data):
        """Update a server's lootboxes"""
        gd = await self.db.get_guild_data(guild)
        gd["lootboxes"] = data
        return await self.db.update_guild_data(guild, gd)

    async def update_guild_guilds(self, guild, data):
        """Update a server's guilds"""
        gd = await self.db.get_guild_data(guild)
        gd["guilds"] = data
        return await self.db.update_guild_data(guild, gd)

    async def remove_guild(self, guild, name):
        gd = await self.db.get_guild_data(guild)
        for mid in gd["guilds"][name][3]:
            try:
                await self.set_guild(Object(id=mid), None)
            except:
                pass
        del gd['guilds'][name]
        return await self.db.update_guild_data(guild, gd)

    async def update_guild_shop(self, guild, data):
        """Update a server's shop"""
        gd = await self.db.get_guild_data(guild)
        gd["shop_items"] = data
        return await self.db.update_guild_data(guild, gd)

    async def add_shop_items(self, guild, data):
        """Update a server's shop"""
        gd = await self.db.get_guild_data(guild)
        gd["shop_items"].update(data)
        return await self.db.update_guild_data(guild, gd)

    async def remove_shop_items(self, guild, *items):
        """Remove a server item"""
        gd = await self.db.get_guild_data(guild)
        for item in items:
            gd["shop_items"].pop(item, None)
        await self.db.update_guild_data(guild, gd)

    async def set_prefix(self, guild, prefix):
        gd = await self.db.get_guild_data(guild)
        gd["prefix"] = prefix
        return await self.db.update_guild_data(guild, gd)

    async def set_cmd_prefixes(self, guild, name, prefix):
        gd = await self.db.get_guild_data(guild)
        if "cmdprefixes" not in gd:
            gd["cmdprefixes"] = {}
        gd["cmdprefixes"][name] = prefix
        return await self.db.update_guild_data(guild, gd)

    async def get_cmd_prefixes(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("cmdprefixes", {})

    async def set_leave_setting(self, guild, prefix):
        gd = await self.db.get_guild_data(guild)
        gd["wipeonleave"] = prefix
        return await self.db.update_guild_data(guild, gd)

    async def get_leave_setting(self, guild):
        gd = await self.db.get_guild_data(guild)
        return gd.get("wipeonleave", False)
