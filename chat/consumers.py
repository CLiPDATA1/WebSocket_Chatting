# chat > consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatConsumer(AsyncWebsocketConsumer):
    # 채팅방 연결
    async def connect(self):
        self.global_group_name = 'global_notice'

        await self.channel_layer.group_add(
            self.global_group_name,
            self.channel_name
        )
        await self.accept()
        logging.info('연결 성공')

    # 채팅방 연결 해제
    async def disconnect(self, close_code):
        await(self.channel_layer.group_discard)(
            self.global_group_name,
            self.channel_name
        )
        logging.info('연결 해제')

    # 메세지 타입에 따라 메시지 포맷팅
    def format_message_by_type(self, message, message_type):
        if message_type == 'NOTICE':
            message = f'{message}'
        elif message_type == 'PAYMENT_A':
            message = f'{message}'
        elif message_type == 'PAYMENT_B':
            message = f'{message}'
        else:
            message_type = 'ETC'
            message = f'{message}'
        return message

    # 채팅방 메시지 전송
    async def  send_global_noti(self, message, message_type):
        formatted_message = self.format_message_by_type(message, message_type)
        
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                'type': 'chat_message',
                'message': formatted_message,
                'message_type': message_type
            }
        )
        
    async def chat_message(self, event):
        message = event['message']
        message_type = event.get('message_type', 'NOTICE')
        
        await self.send(text_data=json.dumps({
            'message': message,
            'message_type': message_type
        }))
        
        logging.info(f'메시지 전송: {message} (타입: {message_type})')

    # 채팅방 메시지 수신
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message_type = text_data_json.get('type', 'NOTICE')
        
        await self.send_global_noti(message, message_type)
        logging.info(f'메시지 수신: {message} (타입: {message_type})')