import os
from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from starlette.middleware.cors import CORSMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rdhs_viz.settings')
django_asgi_app = get_asgi_application()

from rdhs_viz.api import app as fastapi_app

# Main ASGI app routing
async def application(scope, receive, send):
    if scope['type'] in ('http', 'websocket') and scope['path'].startswith('/api'):
        fastapi_scope = dict(scope)
        fastapi_scope['path'] = scope['path'][4:] or '/'
        fastapi_scope['root_path'] = scope.get('root_path', '') + '/api'
        await fastapi_app(fastapi_scope, receive, send)
    else:
        await django_asgi_app(scope, receive, send)
