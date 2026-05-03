
let isStreaming = false;

function sendMessage() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();

    if (!query || isStreaming) return;

    // Add user message
    appendMessage('user', query);
    input.value = '';

    // Show typing indicator
    const typingEl = showTypingIndicator();

    // Stream response from backend
    isStreaming = true;
    toggleInput(false);

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query }),
    })
    .then(response => {
        // Remove typing indicator
        typingEl.remove();

        if (!response.ok) {
            return response.json().then(data => {
                appendMessage('bot', data.error || 'Something went wrong.', true);
                throw new Error('handled');
            });
        }

        // Create bot message bubble for streaming tokens into
        const { bubbleContent } = appendMessage('bot', '');
        let fullText = '';

        // Read the SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function readStream() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    isStreaming = false;
                    toggleInput(true);
                    return;
                }

                const text = decoder.decode(value, { stream: true });
                // Parse SSE format: "data: {...}\n\n"
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));

                            if (data.done) {
                                isStreaming = false;
                                toggleInput(true);
                                return;
                            }

                            if (data.token) {
                                fullText += data.token;
                                bubbleContent.innerHTML = marked.parse(fullText);
                                scrollToBottom();
                            }
                        } catch (e) {
                            // Skip malformed lines
                        }
                    }
                }

                readStream();
            });
        }

        readStream();
    })
    .catch(err => {
        if (err.message !== 'handled') {
            typingEl.remove();
            appendMessage('bot', 'Could not connect to the server. Make sure the backend is running.', true);
        }
        isStreaming = false;
        toggleInput(true);
    });
}

function appendMessage(role, text, isError = false) {
    const container = document.getElementById('chat-container');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message fade-in`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const bubbleContent = document.createElement('div');
    bubbleContent.className = 'bubble-content';
    if (isError) {
        bubbleContent.classList.add('error-text');
    }
    bubbleContent.innerHTML = text ? marked.parse(text) : '';
    bubble.appendChild(bubbleContent);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);

    scrollToBottom();

    return { bubbleContent };
}

function showTypingIndicator() {
    const container = document.getElementById('chat-container');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message fade-in';
    messageDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble typing-indicator';
    bubble.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);

    scrollToBottom();

    return messageDiv;
}

function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

function toggleInput(enabled) {
    document.getElementById('chat-input').disabled = !enabled;
    document.getElementById('send-btn').disabled = !enabled;

    if (enabled) {
        document.getElementById('chat-input').focus();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
