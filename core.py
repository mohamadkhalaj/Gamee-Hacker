import json
import re

from hashlib import md5
from pprint import pprint
from random import randint
from uuid import uuid4

import requests


class GameeHacker:
    SALT = "crmjbjm3lczhlgnek9uaxz2l9svlfjw14npauhen"

    def __init__(self, url, score, play_time):
        self.url = url
        self.score = score
        self.play_time = play_time
        self.game_url = self.extract_game_url()
        self.checksum = self.create_checksum()
        self.uuid = self.create_uuid()
        self.user_auth_token, self.user_id, self.user_personal = self.get_user_credentials()
        self.game_id, self.release_number = self.get_game_data()
        self.response_data = None

    def create_checksum(self):
        raw_data = f"{self.score}:{self.play_time}:{self.game_url}::{__class__.SALT}"
        hash = md5(raw_data.encode()).hexdigest()
        return hash

    def extract_game_url(self):
        groups = re.search('prizes.gamee.com\/game-bot\/(.*)-(.{40})', self.url)
        assert groups != None, 'Invalid Url.'
        groups = groups.groups()
        assert len(groups) == 2, 'Invalid Url.'
        name, token = groups
        game_url = f'/game-bot/{name}-{token}'
        return game_url

    def create_uuid(self):
        return str(uuid4())

    def get_user_credentials(self):
        headers = {
            "X-Install-Uuid": self.uuid,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0",
        }

        data = {
            "jsonrpc": "2.0",
            "id": "user.authentication.botLogin",
            "method": "user.authentication.botLogin",
            "params": {
                "botName": "telegram",
                "botGameUrl": self.game_url,
                "botUserIdentifier": None,
            },
        }

        json_data = json.dumps(data)
        response = requests.post(
            "https://api.service.gameeapp.com/", headers=headers, data=json_data
        ).json()
        user_creds = response["result"]
        user_auth_token = user_creds["tokens"]["authenticate"]
        user_id = user_creds["user"]["id"]
        user_personal = user_creds["user"]["personal"]
        return user_auth_token, user_id, user_personal

    def get_game_data(self):
        headers = {
            "X-Install-Uuid": self.uuid,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0",
        }

        data = {
            "jsonrpc": "2.0",
            "id": "game.getWebGameplayDetails",
            "method": "game.getWebGameplayDetails",
            "params": {"gameUrl": self.game_url},
        }

        json_data = json.dumps(data)
        response = requests.post(
            "https://api.service.gameeapp.com/", headers=headers, data=json_data
        ).json()
        game_data = response["result"]["game"]
        game_id = game_data["id"]
        release_number = game_data["release"]["number"]
        return game_id, release_number

    def get_user_rank(self):
        if self.check_post_status():
            rankings = self.response_data["result"]["surroundingRankings"][0]["ranking"]
            for ranking in rankings:
                if ranking["user"]["id"] == self.user_id:
                    return ranking["rank"]
        return None

    def get_user_record(self):
        if self.check_post_status():
            rankings = self.response_data["result"]["surroundingRankings"][0]["ranking"]
            for ranking in rankings:
                if ranking["user"]["id"] == self.user_id:
                    return ranking["score"]
        return None

    def check_post_status(self):
        if not self.response_data or "error" in str(self.response_data):
            return False
        return True

    def get_data_pprint(self):
        pprint(self.response_data)

    def get_user_summery_pprint(self):
        pprint(self.get_user_summery())
        print("\n")

    def get_user_summery(self):
        user_record = self.get_user_record()
        user_rank = self.get_user_rank()
        temp_data = self.user_personal
        temp_data["record"] = user_record
        temp_data["rank"] = user_rank
        return temp_data

    def send_score(self):
        headers = {
            "Host": "api.service.gameeapp.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"Bearer {self.user_auth_token}",
            "X-Install-Uuid": self.uuid,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "jsonrpc": "2.0",
            "id": "game.saveWebGameplay",
            "method": "game.saveWebGameplay",
            "params": {
                "gameplayData": {
                    "gameId": self.game_id,
                    "score": self.score,
                    "playTime": self.play_time,
                    "gameUrl": self.game_url,
                    "metadata": {"gameplayId": randint(1, 500)},
                    "releaseNumber": self.release_number,
                    "gameStateData": None,
                    "createdTime": "2022-04-23T14:15:19+04:30",
                    "checksum": self.checksum,
                    "replayVariant": None,
                    "replayData": None,
                    "replayDataChecksum": None,
                    "gameplayOrigin": "game",
                }
            },
        }
        json_data = json.dumps(data)
        response = requests.post(
            "https://api.service.gameeapp.com/", headers=headers, data=json_data
        ).json()
        self.response_data = response
        return response
