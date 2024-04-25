# chat > consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from .models import CustomUser, Message
from channels.db import database_sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from asgiref.sync import sync_to_async, async_to_sync
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
    async def send_global_noti(self, message, message_type, sender_id):
        await self.channel_layer.group_send(
            self.global_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'message_type': message_type,
                'sender_id': sender_id,
                'exclude_sender': True
            }
        )
        logging.info(f'전체 사용자(발신자 제외)에게 메시지 전송: {message} (타입: {message_type}), 발신자: {sender_id}')
    
    # 사용자의 채널 이름 조회
    @database_sync_to_async
    def get_sender_username(self, sender_id):
        try:
            sender = CustomUser.objects.get(id=sender_id)
            return sender.username
        except CustomUser.DoesNotExist:
            return None
    
    async def get_channel_name(self, user_id):
        try:
            user = await database_sync_to_async(CustomUser.objects.get)(id=user_id)
            return f'user_{user.username}'
        except CustomUser.DoesNotExist:
            return None
    
    # 클라이언트에게 메시지 전송
    async def chat_message(self, event):
        message = event['message']
        message_type = event.get('message_type', 'None')
        sender_id = event['sender_id']
        exclude_sender = event.get('exclude_sender', False)
        textuser = event.get('textuser', '')

        if not exclude_sender or str(self.scope['user'].id) != str(sender_id):
            await self.send(text_data=json.dumps({
                'message': message,
                'message_type': message_type,
                'sender_id': sender_id,
                'sender__username': await self.get_sender_username(sender_id),
                'textuser': textuser
            }))
            logging.info(f'메시지 전송: {message} (타입: {message_type}), 발신자: {sender_id}')

    # 사용자의 채널 이름 조회
    async def send_personal(self, message, message_type, sender_id, textuser):
        recipient = await database_sync_to_async(CustomUser.objects.get)(username=textuser)
        channel_name = await self.get_channel_name(recipient.id)
        if channel_name:
            await self.channel_layer.send(
                channel_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'message_type': message_type,
                    'sender_id': sender_id,
                    'textuser': textuser
                }
            )
            logging.info(f'{textuser}에게 메시지 전송: {message} (타입: {message_type}), 발신자: {sender_id}')
        
    # 읽지 않은 메시지 수 조회
    @database_sync_to_async
    def get_unread_message_count(self, user):
        try:
            count = Message.objects.filter(user=user, is_read=False).count()
            return count
        except Exception as e:
            logging.error(f"읽지 않은 메시지 개수를 가져오지 못했습니다: {e}")
            return 0

    # 메시지를 저장
    async def save_message(self, message, message_type, sender_id, textuser):
        try:
            sender = await database_sync_to_async(CustomUser.objects.get)(id=sender_id)
            if message_type == 'User' and textuser:
                recipient = await database_sync_to_async(CustomUser.objects.get)(username=textuser)
                if recipient.id != sender_id:
                    message_obj = await database_sync_to_async(Message.objects.create)(
                        user=recipient,
                        message=message,
                        message_type=message_type,
                        is_read=False,
                        sender=sender
                    )
                    unread_count = await self.get_unread_message_count(recipient)
                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            'type': 'unread_count_update',
                            'unread_count': unread_count,
                            'recipient_id': recipient.id
                        }
                    )
            else:
                recipients = await database_sync_to_async(lambda: list(CustomUser.objects.exclude(id=sender_id)))()
                for recipient in recipients:
                    message_obj = await database_sync_to_async(Message.objects.create)(
                        user=recipient,
                        message=message,
                        message_type=message_type,
                        is_read=False,
                        sender=sender
                    )
                    unread_count = await self.get_unread_message_count(recipient)
                    await self.channel_layer.group_send(
                        self.global_group_name,
                        {
                            'type': 'unread_count_update',
                            'unread_count': unread_count,
                            'recipient_id': recipient.id
                        }
                    )
        except CustomUser.DoesNotExist:
            logging.error('존재하지 않는 사용자입니다.')
            return
        
    # 알림 카운트 업데이트
    async def unread_count_update(self, event):
        unread_count = event['unread_count']
        recipient_id = event['recipient_id']
        if str(self.scope['user'].id) == str(recipient_id):
            await self.send(text_data=json.dumps({
                'action': 'unread_count_update',
                'unread_count': unread_count
            }))
            logging.info(f"알림 카운트 업데이트: {unread_count}")

    # 메시지 알림 전송
    async def send_message_notification(self, message, message_type, sender_id, textuser):
        recipients = await database_sync_to_async(lambda: list(CustomUser.objects.exclude(id=sender_id)))()
        recipient_channels = []
        for recipient in recipients:
            channel_name = await self.get_channel_name(recipient.id)
            if channel_name:
                recipient_channels.append(channel_name)
                logging.info(f'{recipient.username}에게 메시지 전송: {message} (타입: {message_type}), 발신자: {sender_id}')

        if recipient_channels:
            await self.channel_layer.group_send(
                'global_notice',
                {
                    'type': 'chat_message',
                    'message': message,
                    'message_type': message_type,
                    'sender_id': sender_id,
                    'textuser': textuser
                }
            )

            for recipient in recipients:
                unread_count = await self.get_unread_message_count(recipient)
                channel_name = await self.get_channel_name(recipient.id)
                if channel_name:
                    await self.channel_layer.send(
                        channel_name,
                        {
                            'type': 'unread_count_update',
                            'unread_count': unread_count
                        }
                    )
                    logging.info(f'{recipient.username}의 알림 카운트 업데이트: {unread_count}')
    
    # 메시지를 읽음으로 표시
    @database_sync_to_async
    def message_read(self, message_id, user):
        try:
            message = Message.objects.get(id=message_id, user=user)
            print(message)
            if not message.is_read:
                message.is_read = True
                message.save()
                return True
            else:
                return True  # 이미 읽음 처리된 메시지인 경우 True 반환
        except Message.DoesNotExist:
            logging.error('존재하지 않는 메시지입니다.')
            return False

    # 사용자의 메시지 조회
    @database_sync_to_async
    def fetch_user_messages(self, user):
        try:
            messages = list(Message.objects.filter(user=user, is_read=False).order_by('-created_at').values('id', 'sender__username', 'message', 'message_type', 'is_read', 'created_at'))
            return messages
        except Exception as e:
            logging.error(f"메시지를 가져오지 못했습니다: {e}")
            return []
        
    # 채팅방 메시지 수신
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')
        if action == 'fetch_messages':
            user = self.scope['user']
            messages = await self.fetch_user_messages(user)
            unread_count = await self.get_unread_message_count(user)
            await self.send(text_data=json.dumps({
                'messages': messages,
                'unread_count': unread_count
            }, cls=DjangoJSONEncoder))
        elif action == 'fetch_unread_count':
            user = self.scope['user']
            unread_count = await self.get_unread_message_count(user)
            await self.send(text_data=json.dumps({
                'action': 'unread_count_update',
                'unread_count': unread_count
            }))
        if action == 'send_message':
            message = text_data_json['message'].strip()
            message_type = text_data_json.get('type', 'None')
            textuser = text_data_json.get('textuser', '')
            sender = self.scope['user']
            if message:
                await self.save_message(message, message_type, sender.id, textuser)
                logging.info(f'메시지 수신 및 저장: {message} (타입: {message_type})')
                await self.send_message_notification(message, message_type, sender.id, textuser)
            else:
                logging.info('공백 메시지는 입력할 수 없습니다.')
        if action == 'read':
            message_id = text_data_json.get('message_id')
            if message_id:
                user = self.scope['user']
                read_success = await self.message_read(message_id, user)
                if read_success:
                    await self.send(text_data=json.dumps({
                        'action': 'read_success',
                        'message_id': message_id
                    }))
                    logging.info(f'메시지 {message_id} 읽음 처리 성공')
                else:
                    logging.error(f'메시지 {message_id} 읽음 처리 실패')