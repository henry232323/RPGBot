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
import copy
import dataclasses
import os

import asyncpg
# import ujson as json
import json

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, set):
            super().default(list(o))
        return super().default(o)


class Database:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def dump(data):
        return json.dumps(data, cls=EnhancedJSONEncoder)

    async def connect(self):
        self._conn = await asyncpg.create_pool(
            user=os.environ.get("DATABASE_USER"),
            password=os.environ.get("DATABASE_PASSWORD"),
            database="pokerpg-new",
            host=os.environ.get("DATABASE_HOST"),
            port=os.environ.get("DATABASE_PORT"),
        )

    # User functions
    ########################################################################
    async def user_insert(self, member, data):
        """Create a new user entry with the given data"""
        jd = self.dump({member.guild.id: data})
        req = """INSERT INTO userdata (UUID, info) VALUES ($1, $2)"""
        async with self._conn.acquire() as connection:
            await connection.execute(req, member.id, jd)

    async def user_select(self, member):
        """Select a user's data for a specified server"""
        req = """SELECT info -> $2 FROM userdata WHERE UUID = $1"""
        async with self._conn.acquire() as connection:
            response = await connection.fetchval(req, member.id, str(member.guild.id))
        return json.loads(response) if response else response

    async def user_full_select(self, member):
        """Select a user's data for a specified server"""
        req = """SELECT info FROM userdata WHERE UUID = $1"""
        async with self._conn.acquire() as connection:
            response = await connection.fetchval(req, member.id)
        return json.loads(response) if response else response

    async def user_update(self, member, data):
        """Update a user's data for a specific server"""
        jd = self.dump(data)
        req = """UPDATE userdata
        SET info = $1
        WHERE UUID = $2"""
        async with self._conn.acquire() as connection:
            await connection.execute(req, jd, member.id)

    async def user_exists(self, member):
        """Check if a user has an entry in the db"""
        req = """SELECT info FROM userdata WHERE UUID = $1"""
        async with self._conn.acquire() as connection:
            return bool(await connection.fetchval(req, member.id))

    async def add_user(self, member, data=None):
        """Add a server to the users json, if the user doesn't exist user_insert to make one"""
        if not data:
            data = {member.guild.id: self.bot.default_udata}

        if not await self.user_exists(member):
            await self.user_insert(member, data)
            return

        else:
            values = await self.user_select(member)

        if not values:
            await self.update_user_data(member, data)

    async def update_user_data(self, member, data):
        """Update a user's server data"""
        fs = await self.user_full_select(member)
        if fs:
            fs.update({str(member.guild.id): data})
            await self.user_update(member, fs)
        else:
            await self.user_insert(member, data)

    async def get_user_data(self, member):
        """Get a user's data for a server"""
        data = await self.user_select(member)
        return data if data else copy.copy(self.bot.default_udata)

    async def get_all_user_data(self, member):
        """Get a user's data for all servers"""
        req = """SELECT info FROM userdata WHERE UUID = $1"""
        async with self._conn.acquire() as connection:
            response = await connection.fetchval(req, member.id)
        return json.loads(response) if response else response

    # Server functions
    ########################################################################
    async def guild_insert(self, guild, data):
        """Add a new guild to the db"""
        jd = self.dump(data)
        req = """INSERT INTO guilddata (UUID, info) VALUES ($1, $2)"""
        async with self._conn.acquire() as connection:
            await connection.execute(req, guild.id, jd)

    async def guild_select(self, guild):
        """Get a guild from the db"""
        req = """SELECT info FROM guilddata WHERE UUID = $1"""
        async with self._conn.acquire() as connection:
            response = await connection.fetchval(req, guild.id)
        return json.loads(response) if response else response

    async def guild_update(self, guild, data):
        """Update a guild"""
        jd = self.dump(data)
        req = """UPDATE guilddata
        SET info = $1
        WHERE UUID = $2"""
        async with self._conn.acquire() as connection:
            await connection.execute(req, jd, guild.id)

    async def add_guild(self, guild, data=None):
        """Add a guild to the db"""
        values = await self.guild_select(guild)
        if values:
            return

        if not data:
            data = self.bot.default_servdata

        await self.guild_insert(guild, data)

    async def update_guild_data(self, guild, data):
        # await self.guild_insert(guild, data)
        # upsert
        jd = self.dump(data)
        req = """INSERT INTO guilddata (UUID, info)
        VALUES (
            $1,
            $2
        )
        ON CONFLICT (UUID) 
        DO 
            UPDATE
            SET info = $2;
        """
        async with self._conn.acquire() as connection:
            await connection.execute(req, guild.id, jd)

        # if await self.guild_select(guild):
        #    await self.guild_update(guild, data)
        # else:
        #    await self.guild_insert(guild, data)

    async def get_guild_data(self, guild):
        values = await self.guild_select(guild)
        if values:
            return values
        else:
            req = """SELECT info FROM guilddata WHERE UUID = $1"""
            async with self._conn.acquire() as connection:
                response = await connection.fetchval(req, guild.id)
            data = json.loads(response) if response else response
            if data:
                await self.update_guild_data(guild, data)
                return data
            else:
                await self.update_guild_data(guild, self.bot.default_servdata)
            return copy.deepcopy(self.bot.default_servdata)
            # return await self.get_guild_data(guild)

    async def guild_item(self, guild, name: str):
        req = """SELECT info ->> $1 FROM guilddata WHERE UUID = $2"""
        async with self._conn.acquire() as connection:
            response = await connection.fetchval(req, name, guild.id)
        return response if response else copy.deepcopy(self.bot.default_servdata[name])

    async def user_item(self, member, name: str):
        req = """SELECT info -> $1 ->> $2 FROM userdata WHERE UUID = $3"""
        async with self._conn.acquire() as connection:
            response = await connection.fetchval(req, str(member.guild.id), name, member.id)
        return response if response else copy.copy(self.bot.default_udata[name])
