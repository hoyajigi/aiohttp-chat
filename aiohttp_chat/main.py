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
from aiohttp import WSCloseCode

websockets_key = aiohttp.web.AppKey("websockets_key", List[web.WebSocketResponse])
redis_key = aiohttp.web.AppKey("redis_key", aioredis.Connection)

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def websocket_handler(request):
    last_redis_stream_id = 0
    ws = web.WebSocketResponse()
    ws_ready = ws.can_prepare(request)
    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await ws.prepare(request)

    name = "moomin_" + str(random.randrange(1,100))

    await ws.send_json({'action': 'connect', 'name': name})

    for wss in request.app[websockets_key].values():
        await wss.send_json({'action': 'join', 'name': name})
    request.app[websockets_key][name] = ws

    redis = request.app[redis_key]
    redis_stream_key = "aiohttp:chatstream"

    while True:
        try:
            async with asyncio.timeout(0.01):
                msg = await ws.receive()

                if msg.type == aiohttp.WSMsgType.text:
                    created_id = await redis.xadd(redis_stream_key, {'action': 'sent', 'name': name, 'text': msg.data})
                else:
                    break
        except TimeoutError:
            pass
        
        rmsgstreams = await redis.xread(streams={redis_stream_key: last_redis_stream_id}, count=1, block = 10)
        for rmsgstream in rmsgstreams:
            key, rmsgs = rmsgstream
            for rmsg in rmsgs:
                last_redis_stream_id, msg_payload = rmsg
                msg_payload_name = msg_payload[b'name'].decode('utf-8')
                msg_payload_text = msg_payload[b'text'].decode('utf-8')
                if name != msg_payload_name:
                    await ws.send_json(
                        {'action': 'sent', 'name': msg_payload_name, 'text': msg_payload_text})
                    
    del request.app[websockets_key][name]
    for wss in request.app[websockets_key].values():
        await wss.send_json({'action': 'disconnect', 'name': name})

    return ws



@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: List[Any],
) -> AsyncIterator[None]:
    app = web.Application()
    app[websockets_key] = {}

    async def init_redis(app):
        host = os.environ['REDIS_HOST']
        port = os.environ['REDIS_PORT']
        redis = await aioredis.from_url(
            f"redis://{host}:{port}",
        )
        app[redis_key] = redis

    app.on_startup.append(init_redis)
    # app.on_cleanup.append(dispose_redis)
    
    async def on_shutdown(app):
        for ws in set(app[websockets_key]):
            await ws.close(code=WSCloseCode.GOING_AWAY, message="Server shutdown")
    
    app.on_shutdown.append(on_shutdown)

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