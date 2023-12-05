from aiohttp import web
import aiohttp
import asyncio
import jinja2
import aiohttp_jinja2
import random
from redis import asyncio as aioredis
import json
import os


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

    for wss in request.app['websockets'].values():
        await wss.send_json({'action': 'join', 'name': name})
    request.app['websockets'][name] = ws

    redis = request.app['redis']
    key = "aiohttp:chat"
    histories = await redis.lrange(key, 0, -1)
    for history in histories:
        await ws.send_json(json.loads(history))


    while True:
        msg = await ws.receive()
        await redis.lpush(key, json.dumps({'action': 'sent', 'name': name, 'text': msg.data}))

        if msg.type == aiohttp.WSMsgType.text:
            for wss in request.app['websockets'].values():
                if wss is not ws:
                    await wss.send_json(
                        {'action': 'sent', 'name': name, 'text': msg.data})
        else:
            break

    del request.app['websockets'][name]
    print('%s disconnected.'%name)
    for wss in request.app['websockets'].values():
        await wss.send_json({'action': 'disconnect', 'name': name})

    return ws

async def init_redis():
    host = os.environ['REDIS_HOST']
    port = os.environ['REDIS_PORT']
    redis = await aioredis.from_url(
        f"redis://{host}:{port}",
    )
    return redis

if __name__ == '__main__':
    app = web.Application()
    app['websockets'] = {}
    loop = asyncio.get_event_loop()
    redis = loop.run_until_complete(init_redis())
    app["redis"] = redis
    aiohttp_jinja2.setup(app,
        loader=jinja2.FileSystemLoader(str('aiohttp_chat/templates')))
    app.router.add_get('/', websocket_handler)
    app.router.add_static('/static/',
                        path='aiohttp_chat/static',
                        name='static')
    web.run_app(app)