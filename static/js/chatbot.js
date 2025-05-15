/**
 * Star College Chatbot JavaScript
 * Handles the interaction with the chatbot API and UI updates
 */

class StarCollegeChatbot {
    constructor() {
        this.apiUrl = 'http://localhost:8000/chat';
        this.chatMessages = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-btn');
        this.clearButton = document.querySelector('.chat-header-actions button:first-child');
        this.schoolSelect = document.getElementById('school-select');
        this.fileUpload = document.getElementById('file-upload');
        this.themeToggle = document.getElementById('theme-toggle');
        this.conversationHistory = [];
        
        this.initEventListeners();
        this.initMarked();
    }
    
    initEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Clear chat history
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => this.clearChat());
        }
        
        // Change school theme
        if (this.schoolSelect) {
            this.schoolSelect.addEventListener('change', () => this.updateSchoolTheme());
        }
        
        // File upload
        if (this.fileUpload) {
            this.fileUpload.addEventListener('change', (e) => this.handleFileUpload(e));
        }
        
        // Theme toggle
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => this.toggleDarkMode());
        }
    }
    
    initMarked() {
        // Set up marked.js options for Markdown parsing
        marked.setOptions({
            breaks: true,  // Add line breaks
            gfm: true      // GitHub Flavored Markdown
        });
    }
    
    updateSchoolTheme() {
        const selectedSchool = this.schoolSelect.value;
        const body = document.body;
        
        // Remove all theme classes
        body.classList.remove('boys-high-theme', 'girls-high-theme', 'primary-theme', 'pre-primary-theme');
        
        // Add selected theme class
        switch (selectedSchool) {
            case 'boys-high':
                body.classList.add('boys-high-theme');
                break;
            case 'girls-high':
                body.classList.add('girls-high-theme');
                break;
            case 'primary':
                body.classList.add('primary-theme');
                break;
            case 'pre-primary':
                body.classList.add('pre-primary-theme');
                break;
        }
    }
    
    toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        
        // Update icon
        if (this.themeToggle) {
            const icon = this.themeToggle.querySelector('i');
            if (document.body.classList.contains('dark-mode')) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        }
    }
    
    clearChat() {
        // Keep only the welcome message
        while (this.chatMessages.children.length > 1) {
            this.chatMessages.removeChild(this.chatMessages.lastChild);
        }
    }
    
    async sendMessage() {
        const question = this.userInput.value.trim();
        if (!question) return;
        
        // Add user message
        this.addMessage(question, 'user');
        
        // Add to conversation history
        this.conversationHistory.push({ role: 'user', content: question });
        
        // Clear input
        this.userInput.value = '';
        
        // Add typing indicator
        const typingIndicator = this.createTypingIndicator();
        this.chatMessages.appendChild(typingIndicator);
        this.scrollToBottom();
        
        try {
            // Get selected school
            const selectedSchool = this.schoolSelect ? this.schoolSelect.value : 'all';
            
            // Make API call
            const response = await fetch(`${this.apiUrl}?store_type=chroma`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    question: question,
                    school: selectedSchool,
                    history: this.conversationHistory
                })
            });
            
            // Remove typing indicator
            this.chatMessages.removeChild(typingIndicator);
            
            if (response.ok) {
                const data = await response.json();
                this.addMessage(data.answer, 'bot', true);
                
                // Add bot response to conversation history
                this.conversationHistory.push({ role: 'bot', content: data.answer });
                
                // Add sources if available
                if (data.sources && data.sources.length > 0) {
                    this.addSources(data.sources);
                }
            } else {
                const errorText = await response.text();
                this.addMessage(`Error: ${response.status} - ${errorText}`, 'bot');
            }
        } catch (error) {
            // Remove typing indicator
            this.chatMessages.removeChild(typingIndicator);
            
            // Add error message
            this.addMessage(`Error: ${error.message}`, 'bot');
        }
    }
    
    createTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot';
        typingIndicator.innerHTML = `
            <div class="message-info">
                <div class="message-avatar">SC</div>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        return typingIndicator;
    }
    
    addMessage(text, type, parseMarkdown = false) {
        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        let avatar = type === 'user' ? 'You' : 'SC';
        
        let messageHTML = `
            <div class="message-info">
                <div class="message-avatar">${avatar}</div>
            </div>
            <div class="message-content">
        `;
        
        if (parseMarkdown && type === 'bot') {
            messageHTML += `<div class="markdown">${marked.parse(text)}</div>`;
        } else {
            messageHTML += `<p>${text}</p>`;
        }
        
        messageHTML += `
            </div>
            <div class="message-time">${timeString}</div>
        `;
        
        messageDiv.innerHTML = messageHTML;
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    addSources(sources) {
        let sourcesHtml = '<h5>Sources:</h5><ul>';
        
        sources.forEach(source => {
            const metadata = source.metadata;
            let sourceInfo = '';
            
            if (metadata.source_type === 'web') {
                sourceInfo = `<a href="${metadata.url}" target="_blank">${metadata.title || metadata.url}</a>`;
            } else if (metadata.source_type === 'file') {
                sourceInfo = `File: ${metadata.filename}`;
                if (metadata.page) {
                    sourceInfo += `, Page: ${metadata.page}`;
                }
            }
            
            sourcesHtml += `<li>${sourceInfo}</li>`;
        });
        
        sourcesHtml += '</ul>';
        
        const lastBotMessage = Array.from(this.chatMessages.querySelectorAll('.message.bot')).pop();
        
        if (lastBotMessage) {
            const messageContent = lastBotMessage.querySelector('.message-content');
            
            // Add sources toggle
            const sourcesToggle = document.createElement('div');
            sourcesToggle.className = 'sources-toggle';
            sourcesToggle.textContent = 'Show sources';
            messageContent.appendChild(sourcesToggle);
            
            // Add sources container (hidden by default)
            const sourcesContainer = document.createElement('div');
            sourcesContainer.className = 'sources-container';
            sourcesContainer.style.display = 'none';
            sourcesContainer.innerHTML = sourcesHtml;
            messageContent.appendChild(sourcesContainer);
            
            // Add toggle functionality
            sourcesToggle.addEventListener('click', function() {
                const isHidden = sourcesContainer.style.display === 'none';
                sourcesContainer.style.display = isHidden ? 'block' : 'none';
                sourcesToggle.textContent = isHidden ? 'Hide sources' : 'Show sources';
                this.scrollToBottom();
            }.bind(this));
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Add message about file upload
        this.addMessage(`Uploading file: ${file.name}...`, 'user');
        
        try {
            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.addMessage(`File uploaded successfully: ${data.filename}`, 'bot');
            } else {
                const errorText = await response.text();
                this.addMessage(`Error uploading file: ${response.status} - ${errorText}`, 'bot');
            }
        } catch (error) {
            this.addMessage(`Error uploading file: ${error.message}`, 'bot');
        }
        
        // Clear the file input
        event.target.value = '';
    }
}

// Initialize the chatbot when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.starCollegeChatbot = new StarCollegeChatbot();
});
