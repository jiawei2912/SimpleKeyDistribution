from typing import Dict, Set, Union, List, Tuple

import json
import urllib.request
import os
import io
import zipfile
import logging
import getpass
import time
import socket
import stat
import subprocess

from config import load_config, get_config
from notification import send_webhook_notification
from utils import get_os_dependent_vars

VER_NUM = "1.1.0"
config:Dict = {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    global config
    err_msg = load_config()
    if err_msg:
        logger.error(err_msg)
        return
    config = get_config()

    logger.info(f'Starting Simple Key Distribution {VER_NUM}...')
    logger.info('Configuration settings:')
    logger.info(json.dumps(config, indent=4))

    def run_once():
        if not check_authorised_keys_permissions():
            return
        keys:Set[str] = get_keys()
        if keys is None:
            return
        update_keys(keys)

    if config["USE_INTERNAL_TIMER"]:
        while True:
            run_once()
            time.sleep(config["INTERNAL_TIMER_INTERVAL"])
    else:
        run_once()
    

# Updates the authorized_keys file with the provided keys
def update_keys(keys: Set[str]):
    # This default value shouldn't persist to the final message
    success_msg:str = ""
    err_msg:str = ""

    err_msg, ssh_dir, authorized_keys_path = get_os_dependent_vars()

    if not err_msg:
        # Ensure the .ssh directory exists
        try:
            os.makedirs(ssh_dir, exist_ok=True)
        except IOError as e:
            err_msg = f'Error creating {ssh_dir}: {e}'
            return

    if not err_msg:
        try:
            if config["OVERRIDE_EXISTING_KEYS"]:
                # Write new keys
                with open(authorized_keys_path, 'w') as file:
                    for key in keys:
                        file.write(key + '\n')
                success_msg = f'Synchronised {authorized_keys_path} with reference keys.'
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
                success_msg = f'Updated {authorized_keys_path} with reference keys.'

        except IOError as e:
            msg = f"Error updating authorised keys at {authorized_keys_path}: {e}"

    msg = err_msg if err_msg else success_msg

    if config["ENABLE_WEBHOOK"]: 
        status = "error" if err_msg else "success"
        err = send_webhook_notification(msg, status)
        if err:
            logger.error(err)
    if err_msg:
        logger.error(err_msg)
    else:
        logger.info(success_msg)

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

def check_authorised_keys_permissions() -> bool:
    err_msg, _, authorized_keys_path = get_os_dependent_vars()
    if err_msg:
        logger.error(err_msg)
        return False

    # Check and set permissions if necessary
    if os.name == 'posix':
        current_permissions = stat.S_IMODE(os.lstat(authorized_keys_path).st_mode)
        expected_permissions = stat.S_IRUSR | stat.S_IWUSR
        if current_permissions != expected_permissions:
            try:
                os.chmod(authorized_keys_path, expected_permissions)
            except PermissionError:
                logger.warning(f"Could not set permissions for {authorized_keys_path}. May rquire sudo.")
                return False
    elif os.name == 'nt':
        try:
            # Check current permissions using icacls
            result = subprocess.run(['icacls', authorized_keys_path], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Could not check permissions for {authorized_keys_path}. {result.stderr}")
                return False

            # Parse the output to check if the current user has full control
            current_user = getpass.getuser()
            expected_permission = f"{current_user}:"
            permissions_correct = False
            for line in result.stdout.splitlines():
                if expected_permission in line and "(F)" in line:
                    permissions_correct = True
                    break

            if not permissions_correct:
                # Attempt to set the permissions if they are not as expected
                result = subprocess.run(['icacls', authorized_keys_path, '/inheritance:r', '/grant:r', f'{current_user}:(F)'], capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Could not set permissions for {authorized_keys_path}. May rquire elevation. {result.stderr}")
                    return False
        except Exception as e:
            logger.warning(f"Could not set permissions for {authorized_keys_path}. May rquire elevation. {e}")
            return False
    return True

main()