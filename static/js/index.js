let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let chatSocket;
let current_id = document.body.getAttribute('data-user-id') || 'default_user_id';

function initWebSocket() {
    chatSocket = new WebSocket('ws://' + window.location.host + '/ws/global_notice/');

    chatSocket.onopen = function(e) {
        console.log('WebSocket connected');
        chatSocket.send(JSON.stringify({
            'action': 'fetch_messages',
            'sender_id': current_id
        }));
    };

    // 메시지 수신 시 처리
    chatSocket.onmessage = function(e) {
        var data = JSON.parse(e.data);
        console.log('받은 메시지:', data);
        processMessage(data);

        if (data.action === 'unread_count_update') {
            var unreadCount = data.unread_count;
            console.log('unread_count_update 액션 처리, unreadCount:', unreadCount);
            updateUnreadCount(unreadCount);
        }
    };

    // 메시지 읽음 처리하는 함수
    function markMessageAsRead(messageId) {
        chatSocket.send(JSON.stringify({
            'action': 'read',
            'message_id': parseInt(messageId)
        }));
    }

    // 알림 클릭 이벤트 리스너
    document.querySelector('.notification').addEventListener('click', function(event) {
        var messageId = event.target.dataset.messageId;
        if (messageId) {
            markMessageAsRead(messageId);
        } else {
            chatSocket.send(JSON.stringify({
                'action': 'fetch_messages',
                'sender_id': current_id
            }));
        }
    });

    // 알림 카운트 업데이트 함수
    function updateUnreadCount(count) {
        var badge = document.querySelector('.notification .badge');
        if (badge) {
            console.log('배지 업데이트, count:', count);
            badge.textContent = count.toString();
            badge.style.display = 'inline-block';
        } else {
            console.log('Notification badge element not found');
        }
    }

    // 메시지 전송
    document.querySelector('#chat-message-input').onkeyup = function(e) {
        if (e.keyCode === 13) {
            document.querySelector('#chat-message-submit').click();
        }
    };

    document.querySelector('#chat-message-submit').onclick = function(e) {
        var messageInputDom = document.querySelector('#chat-message-input');
        var messageTypeSelectDom = document.querySelector('#message-type');
        var userinput = document.querySelector('#chat-user-input');
        var message = messageInputDom.value.trim();
        var messageType = messageTypeSelectDom ? messageTypeSelectDom.value : '';
        var textuser = userinput.value.trim();
        if (!message) {
            alert('메시지를 입력해주세요.');
            return;
        }
        chatSocket.send(JSON.stringify({
            'action': 'send_message',
            'message': message,
            'type': messageType,
            'sender_id': current_id,
            'textuser': textuser,
        }));
        messageInputDom.value = '';
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');

        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            setTimeout(() => {
                console.log('Attempting to reconnect...');
                reconnectAttempts++;
                initWebSocket();
            }, 3000);
        } else {
            console.error('Maximum reconnect attempts reached. Refresh the page to try again.');
        }
    };
    function processMessage(data) {
        if (data.action === 'unread_count_update') {
            console.log('unread_count_update 액션 처리');
            updateUnreadCount(data.unread_count);
            console.log('메시지 업데이트:', data.unread_count);
        } else if (data.messages) {
            console.log('messages 데이터 처리');
            updateMessageList(data.messages, data.unread_count);
        } else if (data.action === 'read_success') {
            console.log('read_success 액션 처리');
            removeMessageRow(data.message_id);
            decrementUnreadCount();
        } else if (data.action === 'message_saved') {
            console.log('message_saved 액션 처리');
            var recipientId = data.recipient_id;
            if (recipientId == current_id) {
                // incrementUnreadCount();
                // chatSocket.send(JSON.stringify({
                //     'action': 'fetch_unread_count'
                // }));
            }
        } else {
            console.log('기타 메시지 처리');
            appendChatLog(data.message, data.message_type, data.sender__username, data.textuser);
        }
    }
    
    function updateMessageList(messages, unreadCount) {
        var messageList = document.querySelector('#messageList');
        messageList.innerHTML = '';
        if (Array.isArray(messages)) {
            messages.forEach(function(message) {
                if (!message.is_read) {
                    var date = new Date(message.created_at);
                    var dateString = date.toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'});
                    var row = `<tr data-message-id="${message.id}">
                        <td>${message.message_type}</td>
                        <td>${message.message}</td>
                        <td>${dateString}</td>
                        <td>${message.sender__username}</td>
                        <td>
                            <button type="button" class="btn btn-primary read-button" data-message-id="${message.id}">읽음</button>
                        </td>
                    </tr>`;
                    messageList.innerHTML += row;
                }
            });
            document.querySelectorAll('.read-button').forEach(function(button) {
                button.addEventListener('click', function() {
                    markMessageAsRead(this.dataset.messageId);
                });
            });
        } else {
            console.log('data.messages가 배열이 아닙니다.');
        }
        updateUnreadCount(unreadCount);
    }
    
    function removeMessageRow(messageId) {
        var row = document.querySelector(`tr[data-message-id="${messageId}"]`);
        if (row) {
            row.remove();
        }
    }
    
    function decrementUnreadCount() {
        var badge = document.querySelector('.notification .badge');
        if (badge) {
            var count = parseInt(badge.textContent, 10) || 0;
            badge.textContent = Math.max(count - 1, 0);
        }
    }
    
    function incrementUnreadCount(count) {
        var badge = document.querySelector('.notification .badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        }
    }
    
    function appendChatLog(message, messageType, senderUsername, textuser) {
        var prefix =messageType === 'Notice' ? '공지: ' :
                    messageType === 'User' ? senderUsername + ': ' :
                    messageType === 'Dept_code' ? '부서: ' :
                    messageType === 'Site_code' ? '사업장: ' : '';
        var chatLog = document.querySelector('#chat-log');
        if (chatLog) {
            chatLog.value += (prefix + message + '\n');
        } else {
            console.log('Chat log element not found');
        }
    }
}

// 초기 웹소켓 연결 시작
initWebSocket();