from collections import namedtuple

pokemon = namedtuple("pokemon", ["name", "stats", "meta"])
server_item = namedtuple("server_item", ["name", "description", "meta"])
character = namedtuple("character", ["name", "owner", "team", "meta"])

default_user = {
    "money": 0,
    "box": [],
    "items": dict(),
}

default_server = {
    "start": 0,
    "items": dict(),
    "characters": []
}


class DataInteraction(object):
    def __init__(self, bot):
        self.bot = bot
