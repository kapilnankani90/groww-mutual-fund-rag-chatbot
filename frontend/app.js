// Configure your API backend URL here (leave empty to use relative path for local development)
const BACKEND_API_URL = 'https://groww-mutual-fund-rag-chatbot-production.up.railway.app';

// DOM Elements
const onboardingContainer = document.getElementById('onboarding-container');
const messagesList = document.getElementById('messages-list');
const chatViewport = document.getElementById('chat-viewport');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Example Card Submission Handler
function sendExamplePrompt(promptText) {
    userInput.value = promptText;
    chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
}

// Format markdown links to raw HTML
function formatMarkdownLinks(text) {
    if (!text) return "";
    // Regex for [link name](url)
    return text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}

// Append a message bubble to the viewport
function appendMessage(sender, text, timestamp = null) {
    // Hide onboarding container once first message is sent
    if (onboardingContainer.style.display !== 'none') {
        onboardingContainer.style.display = 'none';
    }

    const wrapper = document.createElement('div');
    wrapper.classList.add('message-wrapper', sender);

    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble');
    
    // Bot responses can contain markdown links
    if (sender === 'bot') {
        bubble.innerHTML = formatMarkdownLinks(text);
    } else {
        bubble.textContent = text;
    }

    const meta = document.createElement('div');
    meta.classList.add('message-metadata');
    
    const time = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    meta.textContent = sender === 'user' ? `Sent at ${time}` : `Response at ${time}`;

    wrapper.appendChild(bubble);
    wrapper.appendChild(meta);
    messagesList.appendChild(wrapper);

    // Auto scroll to bottom
    chatViewport.scrollTop = chatViewport.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const wrapper = document.createElement('div');
    wrapper.classList.add('message-wrapper', 'bot', 'typing-wrapper');

    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble');

    const indicator = document.createElement('div');
    indicator.classList.add('typing-indicator');
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.classList.add('typing-dot');
        indicator.appendChild(dot);
    }

    bubble.appendChild(indicator);
    wrapper.appendChild(bubble);
    messagesList.appendChild(wrapper);
    chatViewport.scrollTop = chatViewport.scrollHeight;
    
    return wrapper;
}

// Form Submission Event Listener
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;

    // Clear input
    userInput.value = '';
    
    // Append User message
    appendMessage('user', message);

    // Show Bot typing indicator
    const typingWrapper = showTypingIndicator();

    try {
        const url = BACKEND_API_URL ? `${BACKEND_API_URL.replace(/\/$/, '')}/api/chat` : '/api/chat';
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        // Remove typing indicator
        typingWrapper.remove();

        if (response.ok) {
            const data = await response.json();
            appendMessage('bot', data.response);
        } else {
            appendMessage('bot', 'I encountered an error connecting to the service. Please try again.');
        }
    } catch (error) {
        // Remove typing indicator
        typingWrapper.remove();
        console.error('Error fetching chat response:', error);
        appendMessage('bot', 'Unable to reach the server. Please verify your connection.');
    }
});
