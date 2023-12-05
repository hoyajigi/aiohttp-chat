# aiohttp-chat

a simple multi-user single-room realtime webchat app using aiohttp and redis-py

## How to run
```
pyenv virtualenv 3.11.6 venv
pyenv shell venv
pip install -e .
cd aiohttp_chat
python -X dev aiohttp_chat/main.py
```