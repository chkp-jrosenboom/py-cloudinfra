import base64
import logging
import os
from functools import partialmethod
from logging.handlers import RotatingFileHandler
from pathlib import Path

import jmespath
import requests
from requests.adapters import HTTPAdapter, Retry

from . import configuration

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "WARNING").upper())

LOGFILE = os.getenv("CLOUDINFRA_LOGFILE")
FORMAT = "[%(asctime)s %(levelname)s %(filename)s->%(funcName)s %(message)s"

if LOGFILE:
    logfile_path = Path(os.path.expandvars(os.path.expanduser(LOGFILE)))
    logfile_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(LOGFILE, maxBytes=(1048576*5), backupCount=7)
    file_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(file_handler)
else:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(stream_handler)

class LoggingRetry(Retry):
    def increment(self, *args, **kwargs):
        if self.total is not None and self.total > 0:
            if "response" in kwargs and kwargs["response"] is not None:
                logger.warning(
                    "Retrying request (retries left: %s, logger-token: %s)",
                    self.total,
                    kwargs["response"].headers.get("logger-token", "No logger token"),
                )
            else:
                logger.warning("Retrying request (retries left: %s)", self.total)
        return super().increment(*args, **kwargs)

class Session:
    def __init__(
        self,
        key=None,
        secret=None,
        app=None,
        base_url="https://cloudinfra-gw-us.portal.checkpoint.com",
        profile_name=None,
        token=None,
        user_auth=None
    ):

        if base_url and key and secret:
            self.config = configuration.Config(base_url, key, secret, app)
        elif profile_name:
            self.config = configuration.FileConfigProvider(
                profile_name=profile_name
            ).load()
        else:
            self.config = configuration.load_default()

        self.user_auth = user_auth or ""

        if token:
            self.token = token
        else:
            if not all(
                hasattr(self.config, attr)
                for attr in ["BASE_URL", "KEY", "SECRET", "APP"]
            ):
                raise TypeError(f"Invalid config: {self.config}")
            self.get_token()

        if app:
            self.config.APP = app

    def get_token(self):
        response = requests.post(
            url=f"{self.config.BASE_URL}/auth/external{self.user_auth}",
            json={"clientId": self.config.KEY, "accessKey": self.config.SECRET},
        )
        try:
            self.token = response.json()["data"]["token"]
            logger.debug("%s", base64.b64decode(self.token.split(".")[1] + "=="))
            logger.debug(
                "Logger token: %s",
                response.headers.get("logger-token", "Error - no logger token"),
            )
            return self.token
        except Exception:
            logger.error(response.text)
            logger.debug(
                "Logger token: %s",
                response.headers.get("logger-token", "Error - no logger token"),
            )
            return None

    def call(
        self,
        endpoint: str,
        data: object = None,
        method: str = "GET",
        query=None,
        **kwargs,
    ):
        session = requests.Session()
        
        allowed_methods = ["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"]
        # WAF uses POST for all requests, so we need to allow it.
        if self.config.APP.startswith("app/waf"):
            allowed_methods.append("POST")

        retries = LoggingRetry(total=10, backoff_factor=0.5, status_forcelist=[429, 503], allowed_methods=allowed_methods)
        session.mount("https://", HTTPAdapter(max_retries=retries))

        headers = kwargs.pop("headers", {}) | {"Authorization": f"Bearer {self.token}"}

        response = session.request(
            method=method,
            url=f"{self.config.BASE_URL}/{self.config.APP}/{endpoint}",
            json=data,
            headers=headers,
            **kwargs,
        )
        # logger.debug("Headers: %s", response.request.headers)
        logger.debug(
            "Logger token: %s", response.headers.get("logger-token", "Error - no logger token")
        )

        if response.status_code == 401:
            self.get_token()
            headers["Authorization"] = f"Bearer {self.token}"
            response = session.request(
                method=method,
                url=f"{self.config.BASE_URL}/{self.config.APP}/{endpoint}",
                json=data,
                headers=headers,
                **kwargs,
            )
            if response.status_code == 401:
                raise RuntimeError(f"401 Authentication failed: {response.text}")
            
        if response.status_code == 204:
            # No content
            return ""
        if response.status_code < 200 or response.status_code > 300:
            logger.error("Unexpected status code: %s, logger-token: %s", response.status_code, response.headers.get("logger-token", "Error - no logger token"))
            raise RuntimeError(
                f"Unexpected status code: {response.status_code}, {response.text}, {response.headers}"
            )
        if response.headers.get("Content-Type").startswith("application/json"):
            result = response.json()
            if query:
                result = jmespath.search(query, result)
        else:
            result = response.text

        return result

    post = partialmethod(call, method="POST")
    get = partialmethod(call, method="GET")
    put = partialmethod(call, method="PUT")
    delete = partialmethod(call, method="DELETE")
    patch = partialmethod(call, method="PATCH")

    def add_user(self, email, name):
        body = {
            "email": email,
            "name": name,
            "roles": {"global": ["871e947b-8db5-4b87-835f-092cb118bf3b"]},
            "role": "admin",
        }
        response = self.post("user", body)
        return response

    def get_users(self):
        response = self.get("user")
        return response

    def get_audit(self):
        response = self.get("audit")
        return response


def main():
    session = Session()
    print(session.get_users())


if __name__ == "__main__":
    main()
