# Simple SSH Key Distribution
- Author: jiawei2912
- Updated: 2025-03-12

## Overview

A simple and lightweight Python script for automating SSH public key distribution across multiple servers with minimal setup.
It pulls authorised SSH public keys from a central configurable location.


## Features

- **Pull-based**: Servers pull keys instead of being pushed keys.
- **Minimal dependencies**: Only requires standard Python libraries
- **Update or Sync**: Can be configured to append or to synchornise (destructive) public keys.
- **Simple Key Setup**: Just point the script to a zip file of text files or a text file. Each text file can contain multiple keys.
- **Webhook**: The script can notify a service via webhook.

## Benefits

- No central server with access to all machines is required.
- No special software required on target servers, just Python 3.
- As the script pulls, it will work on servers behind restrictive NATs or firewalls that restrict incoming traffic.

## Configuration
- USE_INTERNAL_TIMER: If enabled, the script will loop automatically using a Python while sleep loop.
- INTERNAL_TIMER_INTERVAL: Interval is in seconds
- OVERRIDE_EXISTING_KEYS: If true, all keys are synchronised - keys that do not exist in the key server will be removed from this machine
- KEY_SERVER_URL: Must point to a ZIP file of text files or a text file
- ENABLE_WEBHOOK: If true, the script will send a webhook message whenever it updates the keys.
- HOST_NAME: Hostname sent in the webhook message. Defaults to the system hostname.
- WEBHOOK_URL: Webhook url.
- CHECK_PERMS: If true, the script will attempt to validate and fix permissions issues in authroized_keys if necessary.

## Installation
### Get the Files
```
git clone https://github.com/jiawei2912/SimpleKeyDistribution
```
### Configure conf.json
```
cp conf.template.json conf.json
nano conf.json
```
Refer to the configuration section above for explanations of each setting.
### Commentary: Scheduling
If USE_INTERNAL_TIMER is enabled, the script will periodically updating the keys on its own. However, it would be more reliable to rely on the OS to control the script and to achieve this.

On Ubuntu/Debian, consider setting up a systemctl service and a timer.

On Windows, consider using Task Scheduler.