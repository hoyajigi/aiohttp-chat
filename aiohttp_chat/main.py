from aiohttp import web
import aiohttp
import asyncio
import jinja2
import aiohttp_jinja2
import random
from redis import asyncio as aioredis
import json
import os
import aiotools
from contextlib import asynccontextmanager as actxmgr
from typing import (
    Any,
    AsyncIterator,
    Final,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    cast,
)

websockets_key = aiohttp.web.AppKey("websockets_key", Any)
redis_key = aiohttp.web.AppKey("redis_key", Any)

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    ws_ready = ws.can_prepare(request)
    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await ws.prepare(request)

    name = "moomin_" + str(random.randrange(1,100))
    print('%s joined.'%name)

    await ws.send_json({'action': 'connect', 'name': name})

    for wss in request.app[websockets_key].values():
        await wss.send_json({'action': 'join', 'name': name})
    request.app[websockets_key][name] = ws

    redis = request.app[redis_key]
    key = "aiohttp:chat"
    histories = await redis.lrange(key, 0, -1)
    for history in histories:
        await ws.send_json(json.loads(history))


    while True:
        msg = await ws.receive()
        await redis.lpush(key, json.dumps({'action': 'sent', 'name': name, 'text': msg.data}))

        if msg.type == aiohttp.WSMsgType.text:
            for wss in request.app[websockets_key].values():
                if wss is not ws:
                    await wss.send_json(
                        {'action': 'sent', 'name': name, 'text': msg.data})
        else:
            break

    del request.app[websockets_key][name]
    print('%s disconnected.'%name)
    for wss in request.app[websockets_key].values():
        await wss.send_json({'action': 'disconnect', 'name': name})

    return ws

async def init_redis():
    host = os.environ['REDIS_HOST']
    port = os.environ['REDIS_PORT']
    redis = await aioredis.from_url(
        f"redis://{host}:{port}",
    )
    return redis

@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: List[Any],
) -> AsyncIterator[None]:
    app = web.Application()
    app[websockets_key] = {}
    app[redis_key] = await init_redis()
    aiohttp_jinja2.setup(app,
        loader=jinja2.FileSystemLoader(str('aiohttp_chat/templates')))
    app.router.add_get('/', websocket_handler)
    app.router.add_static('/static/',
                        path='aiohttp_chat/static',
                        name='static')
    
    runner = web.AppRunner(app, keepalive_timeout=30.0)
    await runner.setup()
    site = web.TCPSite(
        runner,
        backlog=1024,
        reuse_port=True,
    )
    await site.start()

    try:
        yield
    finally:
        print("shutting down...")

if __name__ == '__main__':
    try:
        aiotools.start_server(
            server_main,
            num_workers=2,
            wait_timeout=5.0,
        )
    finally:
        print("terminated.")