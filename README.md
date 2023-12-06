# aiohttp-chat

a simple multi-user single-room realtime webchat app using aiohttp and redis-py

## How to run
Simple and best
```
docker-compose up
```


web app for dev
```
pyenv virtualenv 3.11.6 venv
pyenv shell venv
pip install -e .
cd aiohttp_chat
REDIS_HOST=localhost REDIS_PORT=6379 python -X dev aiohttp_chat/main.py
```

redis for local dev
```
docker run -p 6379:6379 redis
```

build and run docker manually if you want
```
docker build -t aiohttp-chat:latest . 
docker run -e REDIS_HOST=host.docker.internal -e REDIS_PORT=6379 -d -p 8080:8080 aiohttp-chat
```

## Limitations
* needs webserver (or some reverse proxy)
* needs logging
* testing


