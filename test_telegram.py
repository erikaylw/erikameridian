#!/usr/bin/env python3
import urllib.request, json
# Read the token from the file
with open('/home/ubuntu/.hermes/profiles/sosmed/.env') as f:
    for line in f:
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            token = line.strip().split('=', 1)[1]
            break

url = f'https://api.telegram.org/bot{token}/getMe'
resp = urllib.request.urlopen(url).read()
data = json.loads(resp)
if data.get('ok'):
    bot = data['result']
    print(f'Bot: @{bot["username"]} (ID: {bot["id"]})')
    print(f'Name: {bot.get("first_name", "")}')
    print(f'Can join groups: {bot.get("can_join_groups", False)}')
    print(f'STATUS: OK')
else:
    print(f'ERROR: {data}')
