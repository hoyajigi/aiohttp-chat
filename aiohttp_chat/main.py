from aiohttp import web
import jinja2
import aiohttp_jinja2


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

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

if __name__ == '__main__':
    app = web.Application()
    aiohttp_jinja2.setup(app,
        loader=jinja2.FileSystemLoader(str('aiohttp_chat/templates')))
    app.router.add_get('/', websocket_handler)
    app.router.add_static('/static/',
                        path='aiohttp_chat/static',
                        name='static')
    web.run_app(app)