from config import get_config
import json
import urllib

# Sends a notification to a webhook URL
# Fails silently
def send_webhook_notification(message: str) -> str:
    config = get_config()
    err_msg = ""
    webhook_url = config.get("WEBHOOK_URL")
    if not webhook_url:
        err_msg = "Webhook URL not provided."

    data = json.dumps({
        "hostname": config["HOST_NAME"],
        "message": message
        }).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=data, headers={'content-type': 'application/json'})

    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                err_msg = f"Failed to send webhook notification. Status code: {response.status}"
    except urllib.error.HTTPError as e:
        err_msg = f'HTTP error occurred while sending webhook: {e.code} {e.reason}'
    except urllib.error.URLError as e:
        err_msg = f'URL error occurred while sending webhook: {e.reason}'
    except Exception as e:
        err_msg = f'Error occurred while sending webhook: {e}'

    return err_msg