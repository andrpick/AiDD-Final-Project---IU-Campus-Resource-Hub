// Chatbot widget JavaScript
(function() {
    let conversationHistory = [];
    let isOpen = false;
    
    // Load conversation history from localStorage
    function loadHistory() {
        const saved = localStorage.getItem('chatbot_history');
        if (saved) {
            try {
                conversationHistory = JSON.parse(saved);
            } catch (e) {
                conversationHistory = [];
            }
        }
    }
    
    // Save conversation history to localStorage
    function saveHistory() {
        // Keep only last 20 messages
        if (conversationHistory.length > 20) {
            conversationHistory = conversationHistory.slice(-20);
        }
        localStorage.setItem('chatbot_history', JSON.stringify(conversationHistory));
    }
    
    // Initialize chatbot
    function initChatbot() {
        loadHistory();
        
        // Get elements
        const toggleBtn = document.getElementById('chatbotToggle');
        const chatWidget = document.getElementById('chatbotWidget');
        const chatBody = document.getElementById('chatbotBody');
        const chatInput = document.getElementById('chatbotInput');
        const chatSendBtn = document.getElementById('chatbotSend');
        const chatMinimizeBtn = document.getElementById('chatbotMinimize');
        const chatCloseBtn = document.getElementById('chatbotClose');
        
        if (!toggleBtn || !chatWidget || !chatBody || !chatInput || !chatSendBtn) {
            console.error('Chatbot elements not found');
            return;
        }
        
        // Open/close chatbot
        function openChat() {
            isOpen = true;
            chatWidget.classList.remove('d-none');
            chatInput.focus();
            scrollToBottom();
        }
        
        function closeChat() {
            isOpen = false;
            chatWidget.classList.add('d-none');
        }
        
        toggleBtn.addEventListener('click', function() {
            if (isOpen) {
                closeChat();
            } else {
                openChat();
            }
        });
        
        if (chatMinimizeBtn) {
            chatMinimizeBtn.addEventListener('click', closeChat);
        }
        
        if (chatCloseBtn) {
            chatCloseBtn.addEventListener('click', function() {
                conversationHistory = [];
                saveHistory();
                chatBody.innerHTML = '';
                closeChat();
            });
        }
        
        // Add message to chat
        function addMessage(content, role, isLoading = false) {
            const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = `chat-message mb-3 ${role === 'user' ? 'user-message' : 'assistant-message'}`;
            
            const messageBubble = document.createElement('div');
            messageBubble.className = `message-bubble ${role === 'user' ? 'user-bubble' : 'assistant-bubble'}`;
            if (isLoading) {
                messageBubble.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div><span>' + content + '</span>';
            } else {
                messageBubble.innerHTML = content.replace(/\n/g, '<br>');
            }
            
            messageDiv.appendChild(messageBubble);
            chatBody.appendChild(messageDiv);
            
            scrollToBottom();
            return messageId;
        }
        
        // Add resources cards
        function addResources(resources) {
            const resourcesDiv = document.createElement('div');
            resourcesDiv.className = 'chat-resources mb-3';
            
            resources.forEach(resource => {
                const resourceCard = document.createElement('div');
                resourceCard.className = 'resource-card p-3 mb-2 rounded';
                resourceCard.style.cursor = 'pointer';
                resourceCard.onclick = function() {
                    window.location.href = `/resources/${resource.resource_id}`;
                };
                
                const title = document.createElement('div');
                title.className = 'fw-semibold mb-1';
                title.textContent = resource.title;
                
                const details = document.createElement('div');
                details.className = 'text-muted small';
                let detailsText = `📍 ${resource.location}`;
                if (resource.capacity != null) {
                    detailsText += ` | 👥 ${resource.capacity}`;
                }
                if (resource.rating) {
                    detailsText += ` | ⭐ ${resource.rating.toFixed(1)}`;
                }
                details.textContent = detailsText;
                
                resourceCard.appendChild(title);
                resourceCard.appendChild(details);
                resourcesDiv.appendChild(resourceCard);
            });
            
            chatBody.appendChild(resourcesDiv);
        }
        
        // Scroll to bottom
        function scrollToBottom() {
            setTimeout(() => {
                chatBody.scrollTop = chatBody.scrollHeight;
            }, 100);
        }
        
        // Send message
        function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message to UI
            addMessage(message, 'user');
            
            // Add to history
            conversationHistory.push({ role: 'user', content: message });
            saveHistory();
            
            // Clear input
            chatInput.value = '';
            
            // Show loading indicator
            const loadingId = addMessage('Thinking...', 'assistant', true);
            
            // Send to API
            fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(-10) // Send last 10 messages for context
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading message
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) {
                    loadingEl.remove();
                }
                
                if (data.success) {
                    // Add assistant response
                    addMessage(data.response, 'assistant');
                    conversationHistory.push({ role: 'assistant', content: data.response });
                    
                    // Add resources if available
                    if (data.resources && data.resources.length > 0) {
                        addResources(data.resources);
                    }
                } else {
                    addMessage(data.response || 'I encountered an error. Please try again.', 'assistant');
                }
                
                saveHistory();
                scrollToBottom();
            })
            .catch(error => {
                console.error('Chat error:', error);
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) {
                    loadingEl.remove();
                }
                addMessage('I encountered an error. Please try again.', 'assistant');
                scrollToBottom();
            });
        }
        
        // Send on enter
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        chatSendBtn.addEventListener('click', sendMessage);
        
        // Load conversation history on open
        function displayHistory() {
            chatBody.innerHTML = '';
            if (conversationHistory.length === 0) {
                addMessage('Hello! I\'m Crimson, your AI assistant for the Indiana University Campus Resource Hub. How can I help you today?', 'assistant');
                conversationHistory.push({ role: 'assistant', content: 'Hello! I\'m Crimson, your AI assistant for the Indiana University Campus Resource Hub. How can I help you today?' });
            } else {
                conversationHistory.forEach(msg => {
                    addMessage(msg.content, msg.role);
                });
            }
            scrollToBottom();
        }
        
        // Show history when opening
        toggleBtn.addEventListener('click', function() {
            if (!isOpen) {
                displayHistory();
            }
        });
        
        // Initial display if widget is open (shouldn't happen, but just in case)
        if (!chatWidget.classList.contains('d-none')) {
            displayHistory();
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatbot);
    } else {
        initChatbot();
    }
})();

