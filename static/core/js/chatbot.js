function toggleChatbot() {
    const window = document.getElementById('chatbot-window');
    const btn = document.getElementById('chatbot-btn');
    
    if (window.style.display === 'none') {
        window.style.display = 'flex';
        btn.style.animation = 'none'; // stop pulsing when opened
    } else {
        window.style.display = 'none';
    }
}

function appendMessage(text, isUser) {
    const messagesArea = document.getElementById('chatbot-messages');
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.gap = '0.5rem';
    wrapper.style.alignItems = 'flex-start';
    
    if (isUser) {
        wrapper.style.flexDirection = 'row-reverse';
        wrapper.innerHTML = `
            <div style="width: 30px; height: 30px; background: rgba(59, 130, 246, 0.5); border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; font-size: 0.8rem;">
                <i class="fas fa-user"></i>
            </div>
            <div style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.3); padding: 0.8rem 1rem; border-radius: 15px; border-top-left-radius: 0; color: white; font-size: 0.9rem; line-height: 1.5;">
                ${text}
            </div>
        `;
    } else {
        wrapper.innerHTML = `
            <div style="width: 30px; height: 30px; background: linear-gradient(135deg, #8b5cf6, #ec4899); border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; font-size: 0.8rem;">
                <i class="fas fa-robot"></i>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 0.8rem 1rem; border-radius: 15px; border-top-right-radius: 0; color: #e2e8f0; font-size: 0.9rem; line-height: 1.5;">
                ${text}
            </div>
        `;
    }
    
    messagesArea.appendChild(wrapper);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    appendMessage(message, true);
    input.value = '';
    
    // Add typing indicator
    const typingId = 'typing-' + Date.now();
    const messagesArea = document.getElementById('chatbot-messages');
    const typingWrapper = document.createElement('div');
    typingWrapper.id = typingId;
    typingWrapper.style.display = 'flex';
    typingWrapper.style.gap = '0.5rem';
    typingWrapper.style.alignItems = 'flex-start';
    typingWrapper.innerHTML = `
        <div style="width: 30px; height: 30px; background: linear-gradient(135deg, #8b5cf6, #ec4899); border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; font-size: 0.8rem;">
            <i class="fas fa-robot"></i>
        </div>
        <div style="background: rgba(255,255,255,0.05); padding: 0.8rem 1rem; border-radius: 15px; border-top-right-radius: 0; color: #94a3b8; font-size: 0.9rem; display: flex; gap: 0.3rem;">
            <i class="fas fa-circle" style="font-size: 0.4rem; animation: bounce 1s infinite;"></i>
            <i class="fas fa-circle" style="font-size: 0.4rem; animation: bounce 1s infinite 0.2s;"></i>
            <i class="fas fa-circle" style="font-size: 0.4rem; animation: bounce 1s infinite 0.4s;"></i>
        </div>
    `;
    messagesArea.appendChild(typingWrapper);
    messagesArea.scrollTop = messagesArea.scrollHeight;
    
    const csrftoken = getCookie('csrftoken');

    fetch('/ai/chat/', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken 
        },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById(typingId).remove();
        if (data.error) {
            appendMessage("عذراً، حدث خطأ أثناء الاتصال.", false);
        } else {
            appendMessage(data.response, false);
        }
    })
    .catch(err => {
        document.getElementById(typingId).remove();
        appendMessage("عذراً، الخادم غير متصل حالياً.", false);
    });
}
