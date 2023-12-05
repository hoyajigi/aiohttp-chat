# aiohttp-chat

a simple multi-user single-room realtime webchat app using aiohttp and redis-py

## How to run
web app for dev
```
pyenv virtualenv 3.11.6 venv
pyenv shell venv
pip install -e .
cd aiohttp_chat
python -X dev aiohttp_chat/main.py
```

redis for local dev
```
docker run -p 6379:6379 redis
```

## Limitations
* needs webserver (or some reverse proxy)
* needs logging
* testing


