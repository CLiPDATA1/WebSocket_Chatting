# chat > consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatConsumer(AsyncWebsocketConsumer):
    # 채팅방 연결
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

        logging.info('연결 성공')

    # 채팅방 연결 해제
    async def disconnect(self, close_code):
        await(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        
        logging.info('연결 해제')

    # 채팅방 메시지 전송
    async def chat_message(self, event):
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'message': message
        }))
        logging.info(f'메시지 전송: {message}')

    # 채팅방 메시지 수신
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        logging.info(f'메시지 수신: {message}')