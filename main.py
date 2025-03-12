from typing import Dict, Set, Union, List

import json
import urllib.request
import os
import io
import zipfile
import logging
import getpass
import time

VER_NUM = "1.0.0"
config:Dict = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_config(file_path) -> bool:
    global config
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
            return True
    except IOError as e:
        logger.error(f'Error reading config file at {file_path}: {e}')
        return False

def main():
    if not load_config('conf.json'): 
        return
    print(f'Starting Simple Key Distribution {VER_NUM}...')
    logger.info(f'Starting Simple Key Distribution {VER_NUM}...')
    logger.info('Configuration settings:')
    logger.info(json.dumps(config, indent=4))
    if config["USE_INTERNAL_TIMER"]:
        while True:
            update_keys(keys)
            time.sleep(config["UPDATE_INTERVAL"])
            keys = get_keys()
            if keys is None:
                continue
    else:
        keys:Set[str] = get_keys()
        if keys is None:
            return
        update_keys(keys)

# Raises an issue if mandatory keys are missing from the config
# Sets default values for optional keys if they are not present
def process_config() -> bool:
    global config
    mandatory_keys = ["KEY_SERVER_URL"]
    default_config = {
        "_comment": "timer_interval is in seconds",
        "USE_INTERNAL_TIMER": False,
        "INTERNAL_TIMER_INTERVAL": 900,
        "OVERRIDE_EXISTING_KEYS": True,
        "KEY_SERVER_URL": "",
        "SSH_PUBLIC_KEY_TYPES": ["ssh-rsa", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521", "ssh-ed25519"]
    }
    
    if not all(key in config for key in mandatory_keys):
        logger.error(f'Missing mandatory key(s) in config: {mandatory_keys}')
        return False
    for key, value in default_config.items():
        config.setdefault(key, value)
    for key, value in config.items():
        if type(value) != type(default_config[key]):
            logger.error(f'Invalid type for key {key} in config: {type(value)}')
            return False
        
    # Specifically to check the URL (verify formatting)
    if not config["KEY_SERVER_URL"].startswith('http'):
        logger.error('Invalid URL format in config: must start with http or https')
        return False
    elif not config["KEY_SERVER_URL"].startswith("https"):
        logger.warning('HTTP is not recommended. Encryption is recommended to protect against man in the middle attacks.')

    return True
    

# Updates the authorized_keys file with the provided keys
def update_keys(keys: Set[str]):
    if os.name == 'posix':
        ssh_dir = os.path.expanduser(f'~{getpass.getuser()}/.ssh')
        authorized_keys_path = os.path.join(ssh_dir, 'authorized_keys')
    elif os.name == 'nt':
        ssh_dir = os.path.expanduser(f'~{getpass.getuser()}\\.ssh')
        authorized_keys_path = os.path.join(ssh_dir, 'authorized_keys')
    else:
        logger.error('Unsupported OS')
        return

    # Ensure the .ssh directory exists
    try:
        os.makedirs(ssh_dir, exist_ok=True)
    except IOError as e:
        logger.error(f'Error creating {ssh_dir}: {e}')
        return

    try:
        if config["OVERRIDE_EXISTING_KEYS"]:
            # Write new keys
            with open(authorized_keys_path, 'w') as file:
                for key in keys:
                    file.write(key + '\n')
            logger.info(f'Synchronised {authorized_keys_path} with reference keys.')
            print("Keys Synced")
        else:
            # Read existing keys if the file exists
            if os.path.exists(authorized_keys_path):
                with open(authorized_keys_path, 'r') as file:
                    existing_keys = set(file.read().splitlines())
            else:
                existing_keys = set()

            # Append new keys
            with open(authorized_keys_path, 'a') as file:
                for key in keys:
                    if key not in existing_keys:
                        file.write(key + '\n')
            logger.info(f'Updated {authorized_keys_path} with reference keys.')
            print("Keys Updated")

    except IOError as e:
        logger.error(f'Error writing to {authorized_keys_path}: {e}')

# Downloads and parses SSH public keys from the KEY_SERVER_URL
# Expects the URL to point to a zip archive of .txt files or a single .txt file
# The .txt files can contain multiple SSH public keys
def get_keys() -> Union[Set[str], None]:
    url = config["KEY_SERVER_URL"]
    
    # Download the file into memory
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except urllib.error.HTTPError as e:
        logger.error(f'HTTP error occurred: {e.code} {e.reason}')
        return
    except urllib.error.URLError as e:
        logger.error(f'URL error occurred: {e.reason}')
        return
    except ValueError as e:
        logger.error(f'Value error occurred: {e}')
        return
    except TimeoutError as e:
        logger.error(f'Timeout error occurred: {e}')
        return
    
    keys: Set[str] = set()
    malformed_files: List[str] = []

    # Check if the file is a zip file
    if zipfile.is_zipfile(io.BytesIO(data)):
        # Unzip the file
        with zipfile.ZipFile(io.BytesIO(data)) as zip_file:
            for file_info in zip_file.infolist():
                with zip_file.open(file_info) as file:
                    try:
                        keys.update(extract_ssh_keys_from_file(file))
                    except UnicodeDecodeError:
                        malformed_files.append(file_info.filename)
    else:
        try:
            keys.update(extract_ssh_keys_from_file(io.BytesIO(data)))
        except UnicodeDecodeError:
            malformed_files.append('file')

    if malformed_files:
        logger.error(f'Error: Malformed file(s) - could not decode as utf-8: {malformed_files}')
        return None
    
    return keys
            

def extract_ssh_keys_from_file(file) -> Union[Set[str], UnicodeDecodeError]:
    ssh_key_types = config["SSH_PUBLIC_KEY_TYPES"]
    keys: Set[str] = set()

    try:
        content = file.read().decode('utf-8')
        for line in content.splitlines():
            line = line.strip()
            if any(key_type in line for key_type in ssh_key_types):
                keys.add(line)
    except UnicodeDecodeError as e:
        return e

    return keys

main()