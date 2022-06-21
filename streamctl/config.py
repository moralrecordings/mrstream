import configparser
import os

import appdirs

LOCAL_CONFIG_DIR: str = appdirs.user_config_dir("streamctl")
LOCAL_CONFIG_PATH: str = os.path.join(LOCAL_CONFIG_DIR, "streamctl.ini")


def get() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(LOCAL_CONFIG_PATH)
    return config

def set(config: configparser.ConfigParser):
    os.makedirs(LOCAL_CONFIG_DIR)
    with open(LOCAL_CONFIG_PATH, "w") as file:
        config.write(file)
