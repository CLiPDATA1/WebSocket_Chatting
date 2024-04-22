# chat > routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/global_notice/', consumers.ChatConsumer.as_asgi()),
]