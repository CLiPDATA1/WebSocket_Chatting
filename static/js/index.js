var chatSocket = new WebSocket('ws://' + window.location.host + '/ws/global_notice/');
var current_id = document.body.getAttribute('data-user-id');

chatSocket.onopen = function(e) {
    chatSocket.send(JSON.stringify({
        'action': 'fetch_messages',
        'sender_id': current_id
    }));
};

// 메시지 읽음 처리하는 함수
function markMessageAsRead(messageId) {
    chatSocket.send(JSON.stringify({
        'action': 'read',
        'message_id': parseInt(messageId)
    }));
    chatSocket.onmessage = function(e) {
        var data = JSON.parse(e.data);
        if (data.action === 'read_success') {
            var row = document.querySelector(`tr[data-message-id="${messageId}"]`);
            if (row) {
                row.remove(); // 메시지 읽음 처리 후 테이블에서 해당 메시지 삭제
            }
            var badge = document.querySelector('.notification .badge');
            var count = parseInt(badge.textContent, 10) || 0;
            badge.textContent = count - 1;
        }
    };
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

// 메시지 수신 시 처리
chatSocket.onmessage = function(e) {
    var data = JSON.parse(e.data);
    if (data.messages) {
        var messages = data.messages;
        var messageList = document.querySelector('#messageList');
        messageList.innerHTML = '';
        if (Array.isArray(messages)) {
            messages.forEach(function(message) {
                if (!message.is_read) {  // 읽지 않은 메시지만 표시
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
        var badge = document.querySelector('.notification .badge');
        badge.textContent = data.unread_count || '0';
        badge.style.display = 'inline-block';
    } else if (data.action === 'read_success') {
        var messageId = data.message_id;
        var row = document.querySelector(`tr[data-message-id="${messageId}"]`);
        if (row) {
            row.remove();
        }
        var badge = document.querySelector('.notification .badge');
        var count = parseInt(badge.textContent, 10) || 0;
        badge.textContent = Math.max(count - 1, 0);  // 카운트 감소
    } else if (data.action === 'unread_count') {
        var badge = document.querySelector('.notification .badge');
        badge.textContent = data.unread_count || '0';
        badge.style.display = 'inline-block';
    } else {
        var message = data.message;
        var messageType = data.message_type;
        var senderUsername = data.sender__username;
        var prefix =messageType === 'Notice' ? '공지: ' :
                    messageType === 'User' ? senderUsername + ': ' :
                    messageType === 'Dept_code' ? '부서: ' :
                    messageType === 'Site_code' ? '사업장: ' : '';
        document.querySelector('#chat-log').value += (prefix + message + '\n');
        // 알람 카운트 증가
        if (data.sender_id.toString() !== current_id) {
            var badge = document.querySelector('.notification .badge');
            var count = parseInt(badge.textContent, 10) || 0;
            badge.textContent = count + 1;
        }
    }
};

// 소켓 연결 종료 시 처리
chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

// 메시지 전송
document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {
        document.querySelector('#chat-message-submit').click();
    }
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    var messageInputDom = document.querySelector('#chat-message-input');
    var messageTypeSelectDom = document.querySelector('#message-type');
    var message = messageInputDom.value.trim();
    var messageType = messageTypeSelectDom ? messageTypeSelectDom.value : '';
    if (!message) {
        alert('메시지를 입력해주세요.');
        return;
    }
    chatSocket.send(JSON.stringify({
        'action': 'send_message',
        'message': message,
        'type': messageType,
        'sender_id': current_id
    }));
    messageInputDom.value = '';
};
