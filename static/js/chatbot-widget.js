/**
 * Star College Chatbot Widget
 * A lightweight version that can be embedded in any page
 */

class StarCollegeChatbotWidget {
    constructor(options = {}) {
        this.options = {
            apiUrl: 'http://localhost:8000/chat',
            containerId: 'chatbot-widget-container',
            position: 'bottom-right',
            title: 'Star College Assistant',
            welcomeMessage: 'Hello! How can I help you with Star College information today?',
            theme: 'light',
            ...options
        };
        
        this.isOpen = false;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        // Create widget container if it doesn't exist
        let container = document.getElementById(this.options.containerId);
        
        if (!container) {
            container = document.createElement('div');
            container.id = this.options.containerId;
            document.body.appendChild(container);
        }
        
        // Add position class
        container.className = `chatbot-widget-container ${this.options.position} ${this.options.theme}`;
        
        // Create widget HTML
        this.createWidgetHTML(container);
        
        // Initialize event listeners
        this.initEventListeners();
        
        this.isInitialized = true;
    }
    
    createWidgetHTML(container) {
        container.innerHTML = `
            <div class="chatbot-widget-button" id="chatbot-widget-button">
                <div class="chatbot-widget-icon">
                    <i class="fas fa-comment"></i>
                </div>
            </div>
            
            <div class="chatbot-widget-box" id="chatbot-widget-box" style="display: none;">
                <div class="chatbot-widget-header">
                    <div class="chatbot-widget-title">
                        <div class="chatbot-widget-logo">
                            <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                                <polygon points="50,5 20,25 20,75 50,95 80,75 80,25" fill="#0a3d62" stroke="#fff" stroke-width="2"/>
                                <polygon points="50,15 30,30 30,70 50,85 70,70 70,30" fill="#e74c3c" stroke="#fff" stroke-width="1"/>
                            </svg>
                        </div>
                        <h3>${this.options.title}</h3>
                    </div>
                    <div class="chatbot-widget-actions">
                        <button class="chatbot-widget-minimize" id="chatbot-widget-minimize">
                            <i class="fas fa-minus"></i>
                        </button>
                    </div>
                </div>
                
                <div class="chatbot-widget-messages" id="chatbot-widget-messages">
                    <div class="chatbot-widget-message bot">
                        <div class="chatbot-widget-message-content">
                            ${this.options.welcomeMessage}
                        </div>
                    </div>
                </div>
                
                <div class="chatbot-widget-input">
                    <input type="text" id="chatbot-widget-input" placeholder="Type your question...">
                    <button id="chatbot-widget-send">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Add styles
        if (!document.getElementById('chatbot-widget-styles')) {
            const styleSheet = document.createElement('style');
            styleSheet.id = 'chatbot-widget-styles';
            styleSheet.textContent = this.getStyles();
            document.head.appendChild(styleSheet);
        }
    }
    
    getStyles() {
        return `
            .chatbot-widget-container {
                position: fixed;
                z-index: 9999;
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            }
            
            .chatbot-widget-container.bottom-right {
                right: 20px;
                bottom: 20px;
            }
            
            .chatbot-widget-container.bottom-left {
                left: 20px;
                bottom: 20px;
            }
            
            .chatbot-widget-button {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background-color: #0a3d62;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .chatbot-widget-button:hover {
                transform: scale(1.05);
            }
            
            .chatbot-widget-icon {
                color: white;
                font-size: 24px;
            }
            
            .chatbot-widget-box {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 350px;
                height: 450px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            
            .chatbot-widget-container.bottom-left .chatbot-widget-box {
                right: auto;
                left: 0;
            }
            
            .chatbot-widget-header {
                padding: 15px;
                background-color: #0a3d62;
                color: white;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .chatbot-widget-title {
                display: flex;
                align-items: center;
            }
            
            .chatbot-widget-logo {
                margin-right: 10px;
            }
            
            .chatbot-widget-title h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 500;
            }
            
            .chatbot-widget-actions button {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 14px;
                opacity: 0.8;
                transition: opacity 0.3s ease;
            }
            
            .chatbot-widget-actions button:hover {
                opacity: 1;
            }
            
            .chatbot-widget-messages {
                flex-grow: 1;
                padding: 15px;
                overflow-y: auto;
                background-color: #f5f6fa;
            }
            
            .chatbot-widget-message {
                margin-bottom: 15px;
                max-width: 80%;
                animation: fadeIn 0.3s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .chatbot-widget-message.user {
                margin-left: auto;
            }
            
            .chatbot-widget-message-content {
                padding: 10px 12px;
                border-radius: 18px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                position: relative;
                font-size: 14px;
                line-height: 1.5;
            }
            
            .chatbot-widget-message.user .chatbot-widget-message-content {
                background-color: #3498db;
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .chatbot-widget-message.bot .chatbot-widget-message-content {
                background-color: white;
                border: 1px solid #e1e1e1;
                border-bottom-left-radius: 4px;
            }
            
            .chatbot-widget-input {
                padding: 10px 15px;
                border-top: 1px solid #e1e1e1;
                display: flex;
                align-items: center;
            }
            
            .chatbot-widget-input input {
                flex-grow: 1;
                border: none;
                padding: 8px 0;
                outline: none;
                font-family: inherit;
                font-size: 14px;
            }
            
            .chatbot-widget-input button {
                background: none;
                border: none;
                color: #3498db;
                cursor: pointer;
                font-size: 18px;
                margin-left: 10px;
                transition: color 0.3s ease;
            }
            
            .chatbot-widget-input button:hover {
                color: #2980b9;
            }
            
            /* Dark theme */
            .chatbot-widget-container.dark .chatbot-widget-box {
                background-color: #2c3e50;
                color: #f5f6fa;
            }
            
            .chatbot-widget-container.dark .chatbot-widget-header {
                background-color: #1e2b3a;
            }
            
            .chatbot-widget-container.dark .chatbot-widget-messages {
                background-color: #34495e;
            }
            
            .chatbot-widget-container.dark .chatbot-widget-message.bot .chatbot-widget-message-content {
                background-color: #2c3e50;
                border-color: #1e2b3a;
                color: #f5f6fa;
            }
            
            .chatbot-widget-container.dark .chatbot-widget-input {
                border-color: #1e2b3a;
                background-color: #2c3e50;
            }
            
            .chatbot-widget-container.dark .chatbot-widget-input input {
                background-color: transparent;
                color: #f5f6fa;
            }
            
            /* Typing indicator */
            .chatbot-widget-typing {
                display: flex;
                align-items: center;
                padding: 5px 0;
            }
            
            .chatbot-widget-typing-dot {
                width: 6px;
                height: 6px;
                margin: 0 1px;
                background-color: #bbb;
                border-radius: 50%;
                animation: typing-dot 1.4s infinite ease-in-out;
            }
            
            .chatbot-widget-typing-dot:nth-child(1) {
                animation-delay: 0s;
            }
            
            .chatbot-widget-typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .chatbot-widget-typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes typing-dot {
                0%, 60%, 100% {
                    transform: translateY(0);
                    opacity: 0.6;
                }
                30% {
                    transform: translateY(-4px);
                    opacity: 1;
                }
            }
        `;
    }
    
    initEventListeners() {
        // Toggle chatbot on button click
        const button = document.getElementById('chatbot-widget-button');
        const box = document.getElementById('chatbot-widget-box');
        
        button.addEventListener('click', () => {
            this.isOpen = !this.isOpen;
            box.style.display = this.isOpen ? 'flex' : 'none';
            
            if (this.isOpen) {
                // Focus on input when opened
                document.getElementById('chatbot-widget-input').focus();
            }
        });
        
        // Minimize chatbot
        const minimizeButton = document.getElementById('chatbot-widget-minimize');
        minimizeButton.addEventListener('click', () => {
            this.isOpen = false;
            box.style.display = 'none';
        });
        
        // Send message
        const sendButton = document.getElementById('chatbot-widget-send');
        const input = document.getElementById('chatbot-widget-input');
        
        const sendMessage = () => {
            const message = input.value.trim();
            if (message) {
                this.addMessage(message, 'user');
                input.value = '';
                this.processMessage(message);
            }
        };
        
        sendButton.addEventListener('click', sendMessage);
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    addMessage(text, type) {
        const messagesContainer = document.getElementById('chatbot-widget-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-widget-message ${type}`;
        
        messageDiv.innerHTML = `
            <div class="chatbot-widget-message-content">
                ${text}
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageDiv;
    }
    
    addTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-widget-messages');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-widget-message bot';
        typingDiv.id = 'chatbot-typing-indicator';
        
        typingDiv.innerHTML = `
            <div class="chatbot-widget-message-content">
                <div class="chatbot-widget-typing">
                    <div class="chatbot-widget-typing-dot"></div>
                    <div class="chatbot-widget-typing-dot"></div>
                    <div class="chatbot-widget-typing-dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return typingDiv;
    }
    
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('chatbot-typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    async processMessage(message) {
        // Add typing indicator
        this.addTypingIndicator();
        
        try {
            // Make API call
            const response = await fetch(this.options.apiUrl + '?store_type=chroma', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    question: message,
                    school: 'all'
                })
            });
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            if (response.ok) {
                const data = await response.json();
                this.addMessage(data.answer, 'bot');
            } else {
                const errorText = await response.text();
                this.addMessage(`Error: ${response.status} - ${errorText}`, 'bot');
            }
        } catch (error) {
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Add error message
            this.addMessage(`Error: ${error.message}`, 'bot');
        }
    }
    
    open() {
        if (!this.isOpen) {
            document.getElementById('chatbot-widget-button').click();
        }
    }
    
    close() {
        if (this.isOpen) {
            document.getElementById('chatbot-widget-minimize').click();
        }
    }
    
    toggle() {
        document.getElementById('chatbot-widget-button').click();
    }
}

// Initialize the widget
window.StarCollegeChatbotWidget = StarCollegeChatbotWidget;
