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

## Benefits

- No central server with access to all machines is required.
- No special software required on target servers, just Python 3.
- As the script pulls, it will work on servers behind restrictive NATs or firewalls that restrict incoming traffic.

## Configuration
```json
{
    "USE_INTERNAL_TIMER": false, // If enabled, the script will loop automatically using a Python while sleep loop.
    "INTERNAL_TIMER_INTERVAL": 900, // Interval is in seconds
    "OVERRIDE_EXISTING_KEYS": true, // If true, all keys are synchronised - keys that do not exist in the key server will be removed from this machine
    "KEY_SERVER_URL": "https://download_path_here", // Must point to a ZIP file of text files or a text file
    "SSH_PUBLIC_KEY_TYPES": [
        "ssh-rsa",
        "ecdsa-sha2-nistp256",
        "ecdsa-sha2-nistp384",
        "ecdsa-sha2-nistp521",
        "ssh-ed25519"
    ]
}
```

