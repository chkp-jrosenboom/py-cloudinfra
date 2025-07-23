import configparser
import os
import pathlib
from dataclasses import dataclass

ENV_NAMES = {
    "BASE_URL": "CLOUDINFRA_URL",
    "KEY": "CLOUDINFRA_KEY",
    "SECRET": "CLOUDINFRA_SECRET",
    "PROFILE": "CLOUDINFRA_PROFILE",
    "APP": "CLOUDINFRA_APP",
}

DEFAULTS = {
    "BASE_URL": "https://cloudinfra-gw-us.portal.checkpoint.com",
    "APP": "api/v1",
    "PROFILE": "default",
}

DEFAULT_CONFIG_FILE = "~/.cloudinfra/credentials"


@dataclass
class Config:
    BASE_URL: str
    KEY: str
    SECRET: str
    APP: str


class ConfigProvider:
    def load(self) -> Config:
        return True


class EnvironmentConfigProvider(ConfigProvider):
    def __init__(self):
        pass

    def load(self) -> Config:
        base_url = os.environ.get(ENV_NAMES["BASE_URL"])
        key = os.environ.get(ENV_NAMES["KEY"])
        secret = os.environ.get(ENV_NAMES["SECRET"])
        app = os.environ.get(ENV_NAMES["APP"], DEFAULTS["APP"])
        if base_url and key and secret:
            return Config(base_url, key, secret, app)


class FileConfigProvider:
    def __init__(self, config_file: str = None, profile_name: str = None) -> None:
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = (
                os.environ.get("CLOUDINFRA_SHARED_CREDENTIALS_FILE")
                or DEFAULT_CONFIG_FILE
            )

        self.config_parser = configparser.ConfigParser()

        if profile_name:
            self.profile_name = profile_name
        else:
            self.profile_name = os.environ.get(
                ENV_NAMES["PROFILE"], DEFAULTS["PROFILE"]
            )

    def load(self) -> Config:
        try:
            self.config_parser.read(pathlib.Path(self.config_file).expanduser())
        except FileNotFoundError:
            return None

        if not self.config_parser.has_section(self.profile_name):
            raise configparser.NoSectionError(self.profile_name)

        base_url = self.config_parser[self.profile_name].get(
            ENV_NAMES["BASE_URL"]
        ) or self.config_parser[DEFAULTS["PROFILE"]].get(
            ENV_NAMES["BASE_URL"], DEFAULTS["BASE_URL"]
        )

        key = self.config_parser[self.profile_name].get(ENV_NAMES["KEY"])
        secret = self.config_parser[self.profile_name].get(ENV_NAMES["SECRET"])
        app = self.config_parser[self.profile_name].get(
            ENV_NAMES["APP"], DEFAULTS["APP"]
        )

        if base_url and app:
            return Config(base_url, key, secret, app)

DEFAULT_PROVIDERS = [
    EnvironmentConfigProvider,
    FileConfigProvider,
]


def load_default(providers: Config = DEFAULT_PROVIDERS):
    for provider in providers:
        config = provider().load()
        if config:
            return config

    raise RuntimeError(
        f"Failed to load configuration. Tried: {', '.join(p.__name__ for p in providers)}"
    )


def list_profiles(config_file: str = None):
    if not config_file:
        config_file = DEFAULT_CONFIG_FILE
    config = configparser.ConfigParser()
    config.read(pathlib.Path(config_file).expanduser())

    return config.sections()
