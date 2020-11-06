import asyncio
import logging
import secrets
from urllib.parse import urlencode, unquote

import aiohttp
import discord
from aiohttp import web

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

try:
    import ujson as json
except ImportError:
    import json

example_post = {
    "bot_id": 305177429612298242,
    "to_bot": "Tatsumaki",
    "amount": 5000,
    "user_id": 122739797646245899,
    "server_id": 166349353999532035
}

bot_db = {
    'id': 305177429612298242,
    'url': "http://api.typheus.me",
    'name': "RPGBot",
    'type': 0
}

user_db = {
    'user_id': 122739797646245899,
    'bots': [305177429612298242],
    'token': 'hsbrbrjsjsbe',
    'type': 0,  # 0 for hook 1 for gather
}

example_hook = {
    "from_bot": "RPGBot",
    "amount": 5000,
    "server_id": 166349353999532035,
    "to_bot": "Tatsumaki"
}

register = {
    'user_id': 122739797646245899,
}


class API(web.Application):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool = None

        with open("pyhtml/auth", 'r') as af:
            self.client_id, self.client_secret = json.loads(af.read())

        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)
        self.logger = logging.getLogger('currency-converter')
        self.logger.setLevel(logging.INFO)
        self.handler = logging.FileHandler(filename="transactions.log",
                                           encoding='utf-8',
                                           mode='a')
        self.handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(self.handler)

        with open("pyhtml/register.html") as _rf:
            self.register_html = _rf.read()

        with open("pyhtml/hub.html") as _rf:
            self.hub_html = _rf.read()

        with open("pyhtml/guild.html") as _rf:
            self.guild_html = _rf.read()

        self.add_routes([
            web.get('/code', self.code),
            web.get('/hub', self.hub),
            web.get('/guilds', self.guilds),
            web.get('/authorize', self.mydata),
            web.get('/', self.index),
            web.get('/register', self.register),
            web.get('/add/', self.add),
            web.get('/bots/{snowflake:\d+}/', self.convert),
            web.post('/bots/{snowflake:\d+}/', self.convert),
            web.get('/user/{guild:\d+}/{user:\d+}{tail:.*}', self.getuser),
            web.get('/guild/{guild:\d+}{tail:.*}', self.getguild),
        ])

    async def host(self):  # Start the connection to the DB and then start the Kyoukai server
        await self.bot.db.connect()
        await self.connect()
        # asyncio.ensure_future(eval.repl(self))

        runner = web.AppRunner(self)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 6667)
        await site.start()

    async def connect(self):
        db = "pokerpg"  # "discoin"
        self.pool = self.bot.db._conn

    async def get_botdata(self, snowflake: int):
        async with self.pool.acquire() as connection:
            response = await connection.fetch(
                f"""SELECT * FROM botdata WHERE UUID = $1""", snowflake
            )

        return response

    async def get_userdata(self, snowflake: int):
        async with self.pool.acquire() as connection:
            response = await connection.fetchval(
                f"""SELECT info FROM userdata WHERE UUID= $1""", snowflake
            )

        return json.loads(response)

    async def get_serverdata(self, snowflake: int):
        async with self.pool.acquire() as connection:
            response = await connection.fetchval(
                f"""SELECT info FROM guilddata WHERE UUID = $1""", snowflake
            )

        return json.loads(response)

    async def code(self, request: web.Request):
        if 'code' not in request.query:
            raise web.HTTPFound("/register?" + urlencode({"redirect": request.url}))

        code = request.query["code"]
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://api.typheus.me/hub",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": 'identify guilds'
        }
        response = await self.session.post(
            f"https://discordapp.com/api/oauth2/token",
            data=urlencode(data),
            headers={'Content-Type': "application/x-www-form-urlencoded"}
        )
        js = await response.json()
        if 'error' in js:
            raise web.HTTPServerError(reason=f"Invalid code or redirect {js['error']}")
        token = js['access_token']
        logging.info("Received Discord OAuth2 code, grabbing token")
        raise web.HTTPFound(f"/hub?token={token}")

    async def hub(self, request: web.Request):
        token = request.query.get("token")
        if not token:
            raise web.HTTPFound("/register?" + urlencode({"redirect": request.url}))

        api_resp = await self.session.get("https://discordapp.com/api/users/@me",
                                          headers={
                                              "Authorization": f"Bearer {token}",
                                          })
        js = await api_resp.json()
        if "code" in js:
            return web.StreamResponse(reason=js["message"], status=js["code"])
        resp = await self.get_userdata(js['id'])
        guilds = await (await self.session.get("https://discordapp.com/api/users/@me/guilds",
                                               headers={
                                                   "Authorization": f"Bearer {token}",
                                               })).json()

        fguilds = filter(lambda x: x["id"] in resp, guilds)
        servers = "\n".join(f"""
                <button>
                    <a href="/guilds?guild_id={guild["id"]}&token={token}">
                        <img src="https://cdn.discordapp.com/icons/{guild["id"]}/{guild["icon"]}.webp?size=32" />
                        {guild["name"]}
                    </a>
                </button>
                <br />""" for guild in fguilds)

        resp = web.Response(body=(self.hub_html.format(token=token, servers=servers)).encode())
        resp.headers['content-type'] = 'text/html'
        return resp

    async def guilds(self, request: web.Request):
        token = request.query.get("token")
        guild_id = request.query.get("guild_id")
        if not (token and guild_id):
            raise web.HTTPFound("/register")

        if not guild_id.isdigit():
            raise web.HTTPNotFound()
        guild_id = int(guild_id)

        medata = await (await self.session.get("https://discordapp.com/api/users/@me",
                                               headers={
                                                   "Authorization": f"Bearer {token}",
                                               })).json()

        guilds = await (await self.session.get("https://discordapp.com/api/users/@me/guilds",
                                               headers={
                                                   "Authorization": f"Bearer {token}",
                                               })).json()

        guild = self.bot.get_guild(guild_id)

        if "code" in guilds:
            return web.StreamResponse(reason=guilds["message"], status=guilds["code"])

        if str(guild_id) not in (g["id"] for g in guilds):
            raise web.HTTPForbidden()

        try:
            guild_data = await self.get_serverdata(guild_id)
            user_data = (await self.get_userdata(medata["id"]))[str(guild_id)]
        except:
            import traceback
            traceback.print_exc()
            raise web.HTTPBadRequest(reason="oof")

        html = self.guild_html
        start = "Start Money: {}".format(guild_data["start"])
        stats = "Balance: {}\n<br />Level: {}\n<br />Exp: {}".format(user_data["money"], user_data.get("level"),
                                                                     user_data.get("exp"))
        fmap = map(lambda x: f"<li>{x[0]} x{x[1]}</li>", sorted(user_data["items"].items()))
        inventory = "\n".join(fmap)

        req = f"""SELECT (UUID, info->'{guild_id}'->>'money') FROM userdata;"""
        async with self.pool.acquire() as connection:
            resp = await connection.fetch(req)

        users = [(discord.utils.get(await guild.fetch_members(None).flatten(), id=int(x["row"][0])), x["row"][1]) for x in resp if
                 (len(x["row"]) == 2) and (x["row"][1] is not None)]
        users = [x for x in users if x[0]]
        users.sort(key=lambda x: -float(x[1]))

        currency = await self.bot.di.get_currency(guild)
        baltop = "\n".join(f"<li> {y[0]} {y[1]} {currency}</li>" for y in users[:11])
        characters = "\n".join(
            f"<li>{name}</li>" for name, obj in guild_data["characters"].items() if obj[2] == str(medata["id"]))

        hubbutton = """
                <button>
                    <a href="/hub?token={token}">
                        Return to Guilds
                    </a>
                </button>
            """.format(token=token)

        html = html.format(
            start_money=start,
            my_stats=stats,
            my_inventory=inventory,
            baltop=baltop,
            my_characters=characters,
            my_guild="Guild: " + str(user_data["guild"]),
            my_box=None,
            salaries=None,
            items=None,
            other_characters=None,
            guilds=None,
            shop=None,
            market=None,
            lotteries=None,
            hubbutton=hubbutton,
            guildname=guild.name,
        )

        resp = web.Response(body=html.encode())

        resp.headers['content-type'] = 'text/html'
        return resp

    async def mydata(self, request: web.Request):
        # if "token" not in ctx.request.args:
        #    return redirect("/register", code=302)
        token = request.query['token']
        api_resp = await self.session.get("https://discordapp.com/api/users/@me",
                                          headers={
                                              "Authorization": f"Bearer {token}",
                                          })
        js = await api_resp.json()
        if "code" in js:
            return web.StreamResponse(reason=js["message"], status=js["code"])

        async with self.pool.acquire() as connection:
            exists = await connection.fetch(
                f"""SELECT * FROM userdata WHERE user_id = {js['id']};"""
            )

            if exists:
                logging.info(f"Received request to view user info for {js['id']}")
                js = {
                    "user_id": js["id"],
                    "bots": exists[0]["bots"],
                }
            else:
                logging.info(f"Creating new database entry for user {js['id']}")
                token = secrets.token_urlsafe(48)

                await connection.fetch(
                    f"""INSERT INTO userdata VALUES (
                        {js["id"]},
                        ARRAY[]::bigint[],
                        '{token}',
                        0
                    );"""
                )

                js = {
                    "user_id": js["id"],
                    "bots": [],
                    "token": token,
                }

        return web.json_response(js)

    # @server.route("/user/{guild}/{user}/", methods=["GET"])
    async def getuser(self, request: web.Request):
        guild = int(request.match_info['guild'])
        user = int(request.match_info['user'])

        req = f"""SELECT info FROM userdata WHERE UUID = {user}"""
        async with self.bot.db._conn.acquire() as connection:
            response = await connection.fetchval(req)
        if response:
            data = json.loads(response)[str(int(guild))]

            fdata = data
            for item in request.match_info['tail'].split("/"):
                if not item:
                    continue
                try:
                    key = unquote(item)
                    if isinstance(fdata, list):
                        key = int(key)
                    fdata = fdata[key]
                except:
                    raise web.HTTPNotFound()

            return web.json_response(fdata)

        raise web.HTTPForbidden()

    # @server.route("/guild/<int:guild>/", methods=["GET"])
    async def getguild(self, request: web.Request):
        guild = int(request.match_info['guild'])
        req = f"""SELECT info FROM guilddata WHERE UUID = $1"""
        async with self.bot.db._conn.acquire() as connection:
            response = await connection.fetchval(req, guild)
        if response:
            data = json.loads(response)

            fdata = data
            if request.match_info['tail']:
                for item in request.match_info['tail'].split("/"):
                    if not item:
                        continue
                    try:
                        key = unquote(item)
                        if isinstance(fdata, list):
                            key = int(key)
                        fdata = fdata[key]
                    except:
                        raise web.HTTPNotFound()

            return web.json_response(fdata)
        raise web.HTTPForbidden()

    # @server.route("/", methods=["GET"])
    async def index(self, request: web.Request):
        raise web.HTTPSeeOther("/register")

    # @server.route("/register", methods=["GET"])
    async def register(self, request: web.Request):  # Post form to complete registration, GET to see register page
        resp = web.Response(body=self.register_html.encode())
        resp.headers['content-type'] = 'text/html'
        return resp

    # @server.route("/add/", methods=["GET", "POST"])
    async def add(self, request: web.Request):
        if request.method == "POST":
            logging.info("Received request to ADD bot")
            if "Authorization" not in request.headers:
                raise web.HTTPUnauthorized(reason="Failed to provide token!")  # Token was omitted from the headers
            raise web.HTTPServiceUnavailable()
        else:
            raise web.HTTPServiceUnavailable()

    # @server.route("/bots/<int:snowflake>/",
    #              methods=["GET", "POST"])  # Post to `/bots/:bot_id/` with token in headers
    async def convert(self, request: web.Request):
        try:
            snowflake = int(request.match_info['snowflake'])
        except:
            raise web.HTTPBadRequest(reason="Malformed request")

        if request.method == "GET":
            logging.info(f"Received request to view info on bot {snowflake}")
            snowflake = int(snowflake)
            resp = dict((await self.get_botdata(snowflake))[0])
            return web.json_response(resp)
        else:
            try:
                if "Authorization" not in request.headers:
                    raise web.HTTPUnauthorized(reason="Failed to provide token!")  # Token was omitted from the headers

                token = request.headers["Authorization"]  # The user token
                snowflake = int(snowflake)  # The bot snowflake
                req = f"""SELECT * FROM userdata WHERE token = '{token.replace("'", "''")}';"""
                async with self.pool.acquire() as connection:
                    response = await connection.fetch(req)  # Get bots and webhook / gather type
                if response:
                    bots, type = response[0]["bots"], response[0]["type"]
                    if snowflake not in bots:  # That bot is not associated with that token
                        raise web.HTTPUnauthorized(reason="That snowflake is not valid!")

                    formdata = await request.post()

                    async with self.pool.acquire() as connection:
                        name = await connection.fetchval(
                            f"""SELECT name FROM botdata WHERE id = {snowflake};"""
                        )  # Get the bot's name
                        url = await connection.fetchval(
                            f"""SELECT url FROM botdata WHERE name = '{formdata["to_bot"].replace("'", "''")}';"""
                        )  # Get the URL of the bot we're sending to
                    if url is None:  # That bot is not in our database!
                        raise web.HTTPBadRequest(reason="That is an invalid bot!")

                    payload = {
                        "from_bot": name,
                        "amount": formdata["amount"],
                        "to_bot": formdata["to_bot"],
                        "server_id": formdata["server_id"]
                    }
                    dumped = json.dumps(payload, indent=4)

                    logging.info(f"Received request to convert {formdata['amount']} from {name} "
                                 f"to {formdata['to_bot']} on server {formdata['server_id']}")
                    if type == 0:  # If using webhooks
                        try:
                            await self.session.post(url, json=dumped)  # Post the payload to the other bot's URL
                        except Exception as e:
                            raise web.HTTPInternalServerError(reason="An error occurred forwarding to the bot!")

                    return web.json_response(payload)
                else:  # If we don't get a response from the given token, the token doesn't exist
                    raise web.HTTPUnauthorized(reason="Invalid token!")
            except web.HTTPException:
                raise
            except:  # Generic error catching, always gives 400 cause how could it be _my_ issue?
                return web.HTTPBadRequest(reason="An error occurred!")
