import time
import requests
import json
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarzbanBackend:

    def __init__(self):
        self.session = requests.Session()
        self.headers = {"accept": "application/json"}
        self.base_url = "https://marzban.perep.site"  # Замените на ваш URL API
        if not self.headers.get("Authorization"):
            self.authorize()

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}/{path}"
        response = self.session.request(
            "GET", url, verify=False, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f'GET not 200 status_code! {path}')

    def _post(self, path: str, data=None) -> dict:
        url = f"{self.base_url}/{path}"
        if not path == "api/admin/token":
            data = json.dumps(data)
        response = self.session.request(
            "POST", url, headers=self.headers, data=data)
        if response.status_code == 201 or response.status_code == 200:
            return response.json()
        else:
            logger.error(f'POST not 200 status_code! {path}, data: {data}')

    def _put(self, path: str, data=None) -> dict:
        url = f"{self.base_url}/{path}"
        json_data = json.dumps(data)
        response = self.session.put(
            url, headers=self.headers, data=json_data)

        if response.status_code == 200:
            logger.info(f"cmd xray PUT {path}, data: {data}")
            return response.json()
        else:
            logger.error(
                f"cmd xray PUT not 200 status_code! {path}, data: {data}")

    def authorize(self) -> None:
        data = {
            "username": "perep",  # Замените на ваше имя пользователя
            "password": "perep"  # Замените на ваш пароль
        }
        response = self._post("api/admin/token", data=data)
        token = response.get("access_token")
        self.headers["Authorization"] = f"Bearer {token}"
        # logger.info(f"Token obtained: {token}")

    def create_user(self, name: str) -> dict:
        try:
            data = {
                "username": name,
                "proxies": {
                    "vless": {
                        "flow": "xtls-rprx-vision",
                    },
                },
                "inbounds": {
                    "vless": ["VLESS TCP REALITY"],
                },
                "data_limit": 15 * 1024 * 1024 * 1024,
                "data_limit_reset_strategy": "day",
            }
            response = self._post("api/user", data=data)
            return response

        except Exception as e:
            logger.error(f"Ошибка бля: {e}")

    def get_user(self, name: str) -> dict:
        response = self._get(f"api/user/{name}")

        if response:
            user = response.get("username")
            status = response.get("status")
            logger.info(f"get user: {user}, status: {status}")
            return response

    def disable_user(self, name: str) -> dict:
        data = {
            "status": "disabled"
        }
        response = self._put(f"api/user/{name}", data=data)
        if response:
            logger.info(
                f"Disable xray user: {name} success, {response.get('username', 'unknown username')}")
            check = self.get_user(name)
            time.sleep(0.25)
            if check.get("status") != data.get("status"):
                logger.error(
                    f"After disable user {name}, user is not disabled!")
            return response
        else:
            logger.warning(f"xray user {name} not found")
            return {}

    def enable_user(self, name: str) -> dict:
        data = {
            "status": "active"
        }
        response = self._put(f"api/user/{name}", data=data)
        if response:
            logger.info(
                f"Enable xray user: {name} success, {response.get('username', 'unknown username')}")
            return response
        else:
            logger.warning(f"xray user {name} not found")
            return {}


backend = MarzbanBackend()
