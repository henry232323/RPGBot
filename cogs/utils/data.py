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


from collections import Counter
from recordclass import recordclass as namedtuple
import ujson as json
import re
import discord
from discord.ext import commands

Pokemon = namedtuple("Pokemon", ["id", "name", "type", "stats", "meta"])
ServerItem = namedtuple("ServerItem", ["name", "description", "meta"])
Character = namedtuple("Character", ["name", "owner", "description", "level", "team", "meta"])
gc = namedtuple("Guild", ["name", "owner", "description", "members", "bank", "items", "open", "image", "icon", "invites", "mods"])

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


class Guild(gc):
    __slots__ = ()

    def __new__(cls, name, owner, description="", members=None, bank=0, items=None, open=False, image=None, icon=None, invites=None, mods=None):
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
            return 'everyone'
        return await super().convert(ctx, argument)


class NumberConverter(commands.Converter):
    async def convert(self, ctx, argument):
        argument = argument.replace(",", "")
        if not argument.isdigit():
            raise commands.BadArgument("That is not a number!")
        if len(argument) > 10:
            raise commands.BadArgument("That number is much too big! Must be less than 999,999,999")
        return int(argument)


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
    "shop_items": dict()
}

example_pokemon = {
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
    "description": "Used to catch Pokemon, one of the weakest balls",
    "meta": {
        "color": "red and white",
        "rate": 20
    }
}

example_character = {
    "name": "Ash Ketchum",
    "owner": 166349353999532035,
    "description": "Likes to catch pokemons",
    "level": 25,
    "team": [0],
    "meta": {
        "hair": "black",
        "favorite_pokemon": "Pichi",
        "image": "http://pa1.narvii.com/6320/3cf4ee1c3106552c4d8116218d556b97da0da020_128.gif"
    }
}

example_user = {
    "money": 25,
    "box": [
        Pokemon(**example_pokemon)
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


class DataInteraction(object):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    async def get_team(self, guild, character):
        gd = await self.db.get_guild_data(guild)
        character = Character(*gd["characters"][character])
        owner = discord.utils.get(guild.members, id=character.owner)
        ud = await self.db.get_user_data(owner)

        pokemon = [Pokemon(*x) for x in ud["box"] if x[0] in character.team]

        return pokemon

    async def get_box(self, member):
        """Get user's Pokemon box"""
        ub = await self.db.user_item(member, "box")
        return [Pokemon(*x) for x in json.decode(ub)]

    async def get_balance(self, member):
        """Get user's balance"""
        return int(await self.db.user_item(member, "money"))

    async def get_inventory(self, member):
        """Get user's inventory"""
        ui = await self.db.user_item(member, "items")
        return json.decode(ui)

    async def get_user_guild(self, member):
        """Get user's associated guild"""
        ud = await self.db.user_item(member, "guild")
        return ud

    async def get_user_level(self, member):
        """Get user's level"""
        ud = await self.db.get_user_data(member)
        return (ud.get("level", 1), ud.get("exp", 0))

    async def get_pokemon(self, member, id):
        """Get a user's Pokemon with the given ID"""
        box = await self.get_box(member)
        for x in box:
            if x[0] == id:
                return x
        else:
            raise KeyError("Pokemon doesn't exist!")

    async def get_guild_start(self, guild):
        """Get a Server's user starting balance"""
        return (await self.db.get_guild_data(guild))["start"]

    async def get_guild_items(self, guild):
        """Get all the items available in a server"""
        gd = await self.db.get_guild_data(guild)
        return {y: ServerItem(*x) for y,x in gd["items"].items()}

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

    async def get_guild_guilds(self, guild):
        """Get a server's guilds"""
        gd = await self.db.get_guild_data(guild)
        return {y: Guild(*x) for y, x in gd.get("guilds", dict()).items()}

    async def add_pokemon(self, owner, pokemon):
        """Create a Pokemon for a user's box"""
        ud = await self.db.get_user_data(owner)
        if not 'id' in pokemon:
            id = ud["box"][-1]["id"] + 1 if ud["box"] else 0
            ud["box"].append(Pokemon(**pokemon, id=id))
        else:
            id = pokemon['id']
            ud["box"].append(Pokemon(**pokemon))
        await self.db.update_user_data(owner, ud)
        return id

    async def remove_pokemon(self, owner, id):
        """Remove a Pokemon from a user's box"""
        ud = await self.db.get_user_data(owner)
        for x in ud["box"]:
            if x[0] == id:
                break
        else:
            raise ValueError("This is not a valid ID!")
        ud["box"].remove(x)
        await self.db.update_user_data(owner, ud)
        return Pokemon(*x)

    async def new_item(self, guild, serveritem):
        """Create a new server item"""
        gd = await self.db.get_guild_data(guild)
        gd["items"][serveritem.name] = serveritem
        await self.db.update_guild_data(guild, gd)

    async def remove_item(self, guild, item):
        """Remove a server item"""
        gd = await self.db.get_guild_data(guild)
        del gd["items"][item]
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

    async def add_eco(self, member, amount):
        """Give (or take) a user('s) money"""
        ud = await self.db.get_user_data(member)
        ud["money"] += amount
        if ud["money"] < 0:
            raise ValueError("Cannot take more than user has!")
        await self.db.update_user_data(member, ud)
        return ud["money"]

    async def set_eco(self, member, amount):
        """Set a user's balance"""
        ud = await self.db.get_user_data(member)
        ud["money"] = amount
        await self.db.update_user_data(member, ud)
        return ud["money"]

    async def set_start(self, guild, amount):
        """Set a server's user start balance"""
        gd = await self.db.get_guild_data(guild)
        gd["start"] = amount
        await self.db.update_user_data(guild, gd)

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

    async def add_to_team(self, guild, character, id):
        """Add a pokemon to a character's team"""
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

    async def set_level(self, member, level, exp):
        ud = await self.db.get_user_data(member)
        ud["level"] = level
        ud["exp"] = exp
        return await self.db.update_user_data(member, ud)

    async def remove_from_team(self, guild, character, id):
        """Remove a pokemon from a character's team"""
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
            await self.set_guild(discord.utils.get(guild.members, id=mid), None)
        del gd["guilds"][name]
        return await self.db.update_guild_data(guild, gd)

    async def update_guild_shop(self, guild, data):
        """Update a server's market"""
        gd = await self.db.get_guild_data(guild)
        gd["shop_items"] = data
        return await self.db.update_guild_data(guild, gd)