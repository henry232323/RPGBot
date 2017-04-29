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


from collections import namedtuple, Counter
import discord
from discord.ext import commands

Pokemon = namedtuple("Pokemon", ["id", "name", "type", "stats", "meta"])
ServerItem = namedtuple("ServerItem", ["name", "description", "meta"])
Character = namedtuple("Character", ["name", "owner", "description", "level", "team", "meta"])
Guild = namedtuple("Guild", ["name", "owner", "description", "members", "bank", "items", "open", "image", "icon", "invites"])


class Converter(commands.MemberConverter):
    def convert(self):
        if self.argument == 'everyone' or self.argument == '@everyone':
            return 'everyone'
        return super().convert()

default_user = {
    "money": 0,
    "box": [],
    "items": dict(),
    "guild": None
}

default_server = {
    "start": 0,
    "items": dict(),
    "characters": dict(),
    "market_items": dict(),
    "loot_boxes": dict(),
    "guilds": dict()
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

example_guild = {
    "name": "Dank Memers",
    "owner": 166349353999532035,
    "description": "We meme dankely",
    "members": {166349353999532035},
    "bank": 5123890,
    "items": Counter(bananas=5),
    "open": False,
    "invites": set(),
    "image": None,
    "icon": None
}

class DataInteraction(object):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.db

    async def get_team(self, guild, character):
        gd = await self.db.get_guild_data(guild)
        character = Character(*gd["characters"][character])
        owner = discord.utils.get(guild.members, id=character.owner)
        ud = await self.db.get_user_data(owner)

        pokemon = [Pokemon(x) for x in ud["box"] if x[0] in character.team]

        return pokemon

    async def get_box(self, member):
        """Get user's Pokemon box"""
        ud = await self.db.get_user_data(member)
        return list(Pokemon(*x) for x in ud["box"])

    async def get_balance(self, member):
        """Get user's balance"""
        return (await self.db.get_user_data(member))["money"]

    async def get_inventory(self, member):
        """Get user's inventory"""
        ud = await self.db.get_user_data(member)
        return ud["items"]

    async def get_user_guild(self, member):
        """Get user's associated guild"""
        ud = await self.db.get_user_data(member)
        return ud.get("guild")

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
        id = ud["box"][-1].id + 1 if ud["box"] else 0
        ud["box"].append(Pokemon(**pokemon, id=id))
        await self.db.update_user_data(owner, ud)
        return id

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
        if [1 for x in ud["items"].values() if x < 0]:
            raise ValueError("Cannot take more items than the user has!")
        await self.db.update_user_data(member, ud)
        return ud["items"]

    async def add_eco(self, member, amount):
        """Give (or take) a user('s) money"""
        ud = await self.db.get_user_data(member)
        ud["money"] += amount
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
        return await self.db.update_user_data(guild, gd)

    async def add_to_team(self, guild, character, id):
        """Add a pokemon to a character's team"""
        gd = await self.db.get_guild_data(guild)
        character = gd["characters"][character]
        character["team"].append(id)
        if len(character["team"]) > 6:
            raise ValueError("Team is limited to 6!")
        await self.db.update_guild_data(guild, gd)

    async def set_guild(self, member, name):
        ud = await self.db.get_user_data(member)
        ud["guild"] = name
        return await self.bot.update_user_data(member, ud)

    async def remove_from_team(self, guild, character, id):
        """Remove a pokemon from a character's team"""
        gd = await self.db.get_guild_data(guild)
        character = gd["characters"][character]
        character["team"].remove(id)
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
        for mid in gd['members']:
            await self.set_guild(discord.utils.get(guild.members, id=mid), None)
        del gd["guilds"][name]
        return await self.db.update_guild_data(guild, gd)