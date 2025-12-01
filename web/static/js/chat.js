// DOM Elements
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const clearFileBtn = document.getElementById('clearFile');
const sendBtn = document.getElementById('sendBtn');
const exportBtn = document.getElementById('exportBtn');
const clearBtn = document.getElementById('clearBtn');
const messagesContainer = document.getElementById('messages');

// Helper function to detect file type
function getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const voiceFormats = ['mp3', 'wav', 'ogg', 'm4a', 'webm'];
    const imageFormats = ['jpg', 'jpeg', 'png'];
    const documentFormats = ['pdf', 'txt', 'docx'];

    if (voiceFormats.includes(ext)) return 'voice';
    if (imageFormats.includes(ext)) return 'image';
    if (documentFormats.includes(ext)) return 'document';
    return 'unknown';
}

// File input change handler
fileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
        const file = this.files[0];
        const fileType = getFileType(file.name);

        if (fileType === 'voice') {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
            fileName.textContent = `🎤 ${file.name} (${sizeMB} MB)`;
        } else {
            fileName.textContent = file.name;
        }
        clearFileBtn.style.display = 'inline-block';
    }
});

// Clear file button handler
clearFileBtn.addEventListener('click', function() {
    fileInput.value = '';
    fileName.textContent = '';
    clearFileBtn.style.display = 'none';
});

// Add message to chat
function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    if (isUser) {
        messageContent.innerHTML = `<strong>You:</strong> ${escapeHtml(content)}`;
    } else {
        messageContent.innerHTML = `<strong>Assistant:</strong> ${formatBotMessage(content)}`;
    }

    messageDiv.appendChild(messageContent);
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add typing indicator
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typing-indicator';

    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    typingContent.innerHTML = '<span></span><span></span><span></span>';

    typingDiv.appendChild(typingContent);
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `Error: ${message}`;

    messagesContainer.appendChild(errorDiv);
    scrollToBottom();

    // Remove error after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Scroll to bottom of messages
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format bot message (preserve line breaks and basic formatting)
function formatBotMessage(text) {
    // Escape HTML first
    let formatted = escapeHtml(text);

    // Convert line breaks to <br>
    formatted = formatted.replace(/\n/g, '<br>');

    // Make text between ** bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Make text between * italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    return formatted;
}

// Handle form submission
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const message = messageInput.value.trim();
    const file = fileInput.files[0];

    // Validate input
    if (!message && !file) {
        showError('Please enter a message or upload a file');
        return;
    }

    // Display user message
    let displayMessage = message;
    if (file) {
        displayMessage = message
            ? `${message} [Attached: ${file.name}]`
            : `[Uploaded: ${file.name}]`;
    }
    addMessage(displayMessage, true);

    // Clear inputs
    messageInput.value = '';
    fileInput.value = '';
    fileName.textContent = '';
    clearFileBtn.style.display = 'none';

    // Disable send button and update text based on file type
    sendBtn.disabled = true;
    if (file && getFileType(file.name) === 'voice') {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
        const estimatedDuration = sizeMB * 1.0; // Rough estimate: 1 MB ≈ 1 minute
        sendBtn.textContent = estimatedDuration > 5
            ? `Transcribing audio (~${Math.round(estimatedDuration)} min)...`
            : 'Transcribing audio...';
    } else {
        sendBtn.textContent = 'Sending...';
    }

    // Show typing indicator
    addTypingIndicator();

    try {
        // Prepare form data
        const formData = new FormData();
        if (message) {
            formData.append('message', message);
        }
        if (file) {
            formData.append('file', file);
        }

        // Send request
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        if (data.success) {
            // Add bot response
            addMessage(data.response);
        } else {
            // Show error
            showError(data.error || 'An error occurred');
        }

    } catch (error) {
        removeTypingIndicator();
        showError('Failed to connect to server: ' + error.message);
    } finally {
        // Re-enable send button
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        messageInput.focus();
    }
});

// Handle clear chat button
clearBtn.addEventListener('click', async function() {
    if (!confirm('Are you sure you want to clear the conversation?')) {
        return;
    }

    try {
        const response = await fetch('/clear', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            // Clear messages except the initial greeting
            messagesContainer.innerHTML = `
                <div class="message bot-message">
                    <div class="message-content">
                        <strong>Assistant:</strong> Hello! 👋 Welcome! I'm your AI assistant. I'm here to help you with your questions! 😊<br><br>You can ask me questions, upload images, share documents, or send voice messages. How can I help you today?
                    </div>
                </div>
            `;
        } else {
            showError('Failed to clear conversation');
        }
    } catch (error) {
        showError('Failed to clear conversation: ' + error.message);
    }
});

// Handle export chat button
exportBtn.addEventListener('click', async function() {
    try {
        const response = await fetch('/export');
        const data = await response.json();

        if (data.success) {
            // Create a blob and download the file
            const blob = new Blob([data.content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            showError(data.error || 'No conversation to export');
        }
    } catch (error) {
        showError('Failed to export conversation: ' + error.message);
    }
});

// Allow sending with Ctrl+Enter
messageInput.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Focus on message input on page load
window.addEventListener('load', function() {
    messageInput.focus();
});
