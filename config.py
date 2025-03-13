from typing import Dict
import logging
import json
import socket
from copy import deepcopy

CONF_FILE_PATH = 'conf.json'

_config: Dict = {}

def load_config() -> str:
    global _config
    err_msg = ""
    try:
        with open(CONF_FILE_PATH, 'r') as file:
            _config = json.load(file)
        err_msg = process_config()
    except IOError as e:
        err_msg = f'Error reading config file at {CONF_FILE_PATH}: {e}'
    except json.JSONDecodeError as e:
        err_msg = f'Error decoding JSON in config file at {CONF_FILE_PATH}: {e}'
    return err_msg
    
def get_config() -> Dict:
    return deepcopy(_config)

# Raises an issue if mandatory keys are missing from the config
# Sets default values for optional keys if they are not present
def process_config() -> str:
    global _config
    err_msg = ""

    mandatory_keys = ["KEY_SERVER_URL"]
    if _config.get("ENABLE_WEBHOOK", False):
        mandatory_keys.append("WEBHOOK_URL")

    default_config = {
        "_comment": "timer_interval is in seconds",
        "USE_INTERNAL_TIMER": False,
        "INTERNAL_TIMER_INTERVAL": 900,
        "OVERRIDE_EXISTING_KEYS": True,
        "KEY_SERVER_URL": "",
        "SSH_PUBLIC_KEY_TYPES": ["ssh-rsa", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521", "ssh-ed25519"],
        "ENABLE_WEBHOOK": False,
        "HOST_NAME": socket.gethostname(),
        "WEBHOOK_URL": "",
        "CHECK_PERMS": True
    }
    
    if not all(key in _config for key in mandatory_keys):
        err_msg = f'Missing mandatory key(s) in config: {mandatory_keys}'
    for key, value in default_config.items():
        _config.setdefault(key, value)
    for key, value in _config.items():
        if type(value) != type(default_config[key]):
            err_msg = f'Invalid type for key {key} in config: {type(value)}'
        
    # Specifically to check the URL (verify formatting)
    if not _config["KEY_SERVER_URL"].startswith('http'):
        err_msg = 'Invalid URL format in config: must start with http or https'
    elif not _config["KEY_SERVER_URL"].startswith("https"):
        err_msg = 'HTTP is not recommended. Encryption is recommended to protect against man in the middle attacks.'

    return err_msg