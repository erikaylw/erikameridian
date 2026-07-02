import re
path = '/home/ubuntu/.hermes/profiles/sosmed/.env'
with open(path, 'r') as f:
    content = f.read()
new_content = re.sub(
    r'^TELEGRAM_BOT_TOKEN=.*$',
    'TELEGRAM_BOT_TOKEN=8957635841:AAEv8vXxjBTV3U9AZqXXI5Nk8Iu7VPOWN6A',
    content,
    flags=re.MULTILINE
)
with open(path, 'w') as f:
    f.write(new_content)
print('Token updated successfully')
