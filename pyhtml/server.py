import asyncio
import logging
import secrets
from urllib.parse import urlencode

import discord
import aiohttp
from kyoukai import Kyoukai
from kyoukai.util import as_html, as_json
from kyoukai.asphalt import HTTPRequestContext, Response
from werkzeug.exceptions import HTTPException
from werkzeug.utils import redirect

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


class API(Kyoukai):
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

    async def host(self):  # Start the connection to the DB and then start the Kyoukai server
        await self.bot.db.connect()
        await self.connect()
        # asyncio.ensure_future(eval.repl(self))
        await self.start('0.0.0.0', 1996)

    async def connect(self):
        db = "pokerpg"  # "discoin"
        self.pool = self.bot.db._conn

    async def get_botdata(self, snowflake: int):
        async with self.pool.acquire() as connection:
            response = await connection.fetch(
                f"""SELECT * FROM botdata WHERE id = {snowflake};"""
            )

        return response

    async def get_userdata(self, snowflake: int):
        async with self.pool.acquire() as connection:
            response = await connection.fetchval(
                f"""SELECT info FROM userdata WHERE UUID={snowflake};"""
            )

        return json.loads(response)

    async def get_serverdata(self, snowflake: int):
        async with self.pool.acquire() as connection:
            response = await connection.fetchval(
                f"""SELECT info FROM servdata WHERE UUID={snowflake};"""
            )

        return json.loads(response)


def makepaths(server):
    @server.route("/code", methods=["GET"])
    async def code(ctx: HTTPRequestContext):
        if 'code' not in ctx.request.args:
            return redirect("/register?" + urlencode({"redirect": ctx.request.url}), code=302)

        code = ctx.request.args["code"]
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "https://api.typheus.me/hub",
            "client_id": server.client_id,
            "client_secret": server.client_secret
        }
        response = await server.session.post(
            f"https://discordapp.com/api/oauth2/token?{urlencode(data)}",
        )
        js = await response.json()
        if 'error' in js:
            return Response(f"Invalid code or redirect {js['error']}", status=500)
        token = js['access_token']
        logging.info("Received Discord OAuth2 code, grabbing token")
        return redirect(f"/hub?token={token}", code=302)

    @server.route("/hub", methods=["GET"])
    async def hub(ctx: HTTPRequestContext):
        token = ctx.request.args.get("token")
        if not token:
            return redirect("/register?" + urlencode({"redirect": ctx.request.url}))

        api_resp = await server.session.get("https://discordapp.com/api/users/@me",
                                            headers={
                                                "Authorization": f"Bearer {token}",
                                            })
        js = await api_resp.json()
        if "code" in js:
            return Response(js["message"], status=js["code"])
        resp = await server.get_userdata(js['id'])
        guilds = await (await server.session.get("https://discordapp.com/api/users/@me/guilds",
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

        return as_html(server.hub_html.format(token=token, servers=servers))

    @server.route("/guilds", methods=["GET"])
    async def guilds(ctx: HTTPRequestContext):
        token = ctx.request.args.get("token")
        guild_id = ctx.request.args.get("guild_id")
        if not (token and guild_id):
            return redirect("/register")

        if not guild_id.isdigit():
            return Response(status=404)
        guild_id = int(guild_id)

        medata = await (await server.session.get("https://discordapp.com/api/users/@me",
                                                 headers={
                                                     "Authorization": f"Bearer {token}",
                                                 })).json()

        guilds = await (await server.session.get("https://discordapp.com/api/users/@me/guilds",
                                                 headers={
                                                     "Authorization": f"Bearer {token}",
                                                 })).json()

        guild = server.bot.get_guild(guild_id)

        if "code" in guilds:
            return Response(guilds["message"], status=guilds["code"])

        if str(guild_id) not in (g["id"] for g in guilds):
            return Response(status=403)

        try:
            guild_data = await server.get_serverdata(guild_id)
            user_data = (await server.get_userdata(medata["id"]))[str(guild_id)]
        except:
            import traceback
            traceback.print_exc()
            return Response("oof", status=400)

        html = server.guild_html
        start = "Start Money: {}".format(guild_data["start"])
        stats = "Balance: {}\n<br />Level: {}\n<br />Exp: {}".format(user_data["money"], user_data.get("level"),
                                                                     user_data.get("exp"))
        fmap = map(lambda x: f"{x[0]} x{x[1]}", sorted(user_data["items"].items()))
        inventory = "\n".join(fmap)

        req = f"""SELECT (UUID, info->'{guild_id}'->>'money') FROM userdata;"""
        async with server.pool.acquire() as connection:
            resp = await connection.fetch(req)

        users = [(discord.utils.get(guild.members, id=int(x["row"][0])), x["row"][1]) for x in resp if
                 (len(x["row"]) == 2) and (x["row"][1] is not None)]
        users = [x for x in users if x[0]]
        users.sort(key=lambda x: -float(x[1]))

        currency = await server.bot.di.get_currency(guild)
        baltop = "\n".join(f"<li> {y[0]} {y[1]} {currency}</li>" for y in users[:11])
        characters = "\n".join(f"<li>{name}</li>" for name, obj in guild_data["characters"].items() if obj[2] == str(medata["id"]))

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
            my_guild="Guild: " + user_data["guild"],
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
        return as_html(html, code=200)

    @server.route("/authorize", methods=["GET"])
    async def mydata(ctx: HTTPRequestContext):
        # if "token" not in ctx.request.args:
        #    return redirect("/register", code=302)
        token = ctx.request.args['token']
        api_resp = await server.session.get("https://discordapp.com/api/users/@me",
                                            headers={
                                                "Authorization": f"Bearer {token}",
                                            })
        js = await api_resp.json()
        if "code" in js:
            return Response(js["message"], status=js["code"])

        async with server.pool.acquire() as connection:
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

        return as_json(js, code=200)

    @server.route("/user/<int:guild>/<int:user>/", methods=["GET"])
    async def getuser(ctx: HTTPRequestContext, guild: int, user: int):
        req = f"""SELECT info FROM userdata WHERE UUID = {user}"""
        async with server.bot.db._conn.acquire() as connection:
            response = await connection.fetchval(req)
        if response:
            return as_json(json.decode(response)[str(int(guild))], code=200)
        return Response(status=403)

    @server.route("/guild/<int:guild>/", methods=["GET"])
    async def getguild(ctx: HTTPRequestContext, guild: int):
        req = f"""SELECT info FROM servdata WHERE UUID = {guild}"""
        async with server.bot.db._conn.acquire() as connection:
            response = await connection.fetchval(req)
        if response:
            return as_json(json.decode(response), code=200)
        return Response(status=403)

    @server.route("/", methods=["GET"])
    async def index(ctx: HTTPRequestContext):
        return redirect("/register", code=303)

    @server.route("/register", methods=["GET"])
    async def register(ctx: HTTPRequestContext):  # Post form to complete registration, GET to see register page
        return as_html(server.register_html)

    @server.route("/add/", methods=["GET", "POST"])
    async def add(ctx: HTTPRequestContext):
        if ctx.request.method == "POST":
            logging.info("Received request to ADD bot")
            if "Authorization" not in ctx.request.headers:
                return HTTPException("Failed to provide token!",  # Token was omitted from the headers
                                     response=Response("Failed to fetch info!", status=401))
            return Response(status=503)
        else:
            return Response(status=503)

    @server.route("/bots/<int:snowflake>/", methods=["GET", "POST"])  # Post to `/bots/:bot_id/` with token in headers
    async def convert(ctx: HTTPRequestContext, snowflake: int):
        if ctx.request.method == "GET":
            logging.info(f"Received request to view info on bot {snowflake}")
            snowflake = int(snowflake)
            resp = dict((await server.get_botdata(snowflake))[0])
            return as_json(resp, code=200)
        else:
            try:
                if "Authorization" not in ctx.request.headers:
                    return HTTPException("Failed to provide token!",  # Token was omitted from the headers
                                         response=Response("Failed to fetch info!", status=401))
                token = ctx.request.headers["Authorization"]  # The user token
                snowflake = int(snowflake)  # The bot snowflake
                req = f"""SELECT * FROM userdata WHERE token = '{token.replace("'", "''")}';"""
                async with server.pool.acquire() as connection:
                    response = await connection.fetch(req)  # Get bots and webhook / gather type
                if response:
                    bots, type = response[0]["bots"], response[0]["type"]
                    if snowflake not in bots:  # That bot is not associated with that token
                        return HTTPException("That snowflake is not valid!",
                                             Response("Failed to fetch info!", status=401))

                    async with server.pool.acquire() as connection:
                        name = await connection.fetchval(
                            f"""SELECT name FROM botdata WHERE id = {snowflake};"""
                        )  # Get the bot's name
                        url = await connection.fetchval(
                            f"""SELECT url FROM botdata WHERE name = '{ctx.request.form["to_bot"].replace("'", "''")}';"""
                        )  # Get the URL of the bot we're sending to
                    if url is None:  # That bot is not in our database!
                        return HTTPException("That is an invalid bot!",
                                             response=Response("Failed to fetch info!", status=400))

                    payload = {
                        "from_bot": name,
                        "amount": ctx.request.form["amount"],
                        "to_bot": ctx.request.form["to_bot"],
                        "server_id": ctx.request.form["server_id"]
                    }
                    dumped = json.dumps(payload, indent=4)

                    logging.info(f"Received request to convert {ctx.request.form['amount']} from {name} "
                                 f"to {ctx.request.form['to_bot']} on server {ctx.request.form['server_id']}")
                    if type is 0:  # If using webhooks
                        try:
                            await server.session.post(url, json=dumped)  # Post the payload to the other bot's URL
                        except Exception as e:
                            return HTTPException("An error occurred forwarding to the bot!",
                                                 response=Response(e, status=500))

                    return as_json(payload, code=200)
                else:  # If we don't get a response from the given token, the token doesn't exist
                    return HTTPException("Invalid token!", response=Response("Failed to fetch info!", status=401))
            except:  # Generic error catching, always gives 400 cause how could it be _my_ issue?
                return HTTPException("An error occurred!", response=Response("Failed to fetch info!", status=400))
