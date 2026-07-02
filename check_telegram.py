#!/usr/bin/env python3
try:
    import telegram
    print(f'python-telegram-bot version: {telegram.__version__}')
except ImportError:
    print('NOT_INSTALLED')
