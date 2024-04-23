# chat > consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from .models import CustomUser, Message
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import logging
import json

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

    # 전체 사용자에게 메시지 전송
    async def  send_global_noti(self, message, message_type, sender_id):
        
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'message_type': message_type,
                'sender_id': sender_id
            }
        )
    
    # 클라이언트에게 메시지 전송
    async def chat_message(self, event):
        message = event['message']
        message_type = event.get('message_type', 'Notice')
        
        await self.send(text_data=json.dumps({
            'message': message,
            'message_type': message_type
        }))
        logging.info(f'메시지 전송: {message} (타입: {message_type})')

    # 메시지를 저장
    @database_sync_to_async
    def save_message_and_update_badge(self, message, message_type, sender_id):
        try:
            sender = CustomUser.objects.get(id=sender_id)
            Message.objects.create(
                user=sender, 
                message=message, 
                message_type=message_type, 
                is_read=True
            )
        except CustomUser.DoesNotExist:
            logging.error('존재하지 않는 사용자입니다.')
            return
        
        recipients = CustomUser.objects.exclude(id=sender_id)
        
        for user in recipients:
            Message.objects.create(
                user=user, 
                message=message, 
                message_type=message_type, 
                is_read=False
            )
            self.update_badge_count(user.id)
    
    @database_sync_to_async
    def update_badge_count(self, user_id):
        user = CustomUser.objects.get(id=user_id)
        user.badge_count += 1
        user.save()
    
    # 메시지를 읽음으로 표시
    @database_sync_to_async
    def message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if not message.is_read:
                message.is_read = True
                message.save()
                user = message.user
                if user.badge_count > 0:
                    user.badge_count -= 1
                    user.save()
                return True
        except Message.DoesNotExist:
            logging.error('존재하지 않는 메시지입니다.')
            return False
    
    # 채팅방 메시지 수신
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'send_message':
            message = text_data_json['message'].strip()
            message_type = text_data_json.get('type', 'Notice')
            sender = self.scope['user']
            if message:
                await self.save_message_and_update_badge(message, message_type, sender.id)
                logging.info(f'메시지 수신 및 저장: {message} (타입: {message_type})')
                await self.send_global_noti(message, message_type, sender.id)
            else:
                logging.info('공백 메시지는 입력할 수 없습니다.')
                
        elif action == 'read':
            message_id = text_data_json.get('message_id')
            if message_id:
                read_success = await self.message_read(message_id)
                if read_success:
                    logging.info(f'메시지 {message_id} 읽음 처리 성공')
                else:
                    logging.error(f'메시지 {message_id} 읽음 처리 실패')