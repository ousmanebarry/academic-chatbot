class AcademicChatBot {
	constructor() {
		// Use relative URLs for production deployment
		this.baseUrl = window.location.origin;
		this.conversationId = `conv_${Date.now()}`;
		this.isConnected = false;
		this.selectedFiles = [];

		this.initializeElements();
		this.attachEventListeners();
		this.checkConnection();
		this.loadStats();

		// Refresh stats every 10 seconds
		setInterval(() => this.loadStats(), 10000);
	}

	initializeElements() {
		this.chatMessages = document.getElementById('chat-messages');
		this.messageInput = document.getElementById('message-input');
		this.sendBtn = document.getElementById('send-btn');
		this.connectionStatus = document.getElementById('connection-status');
		this.uploadArea = document.getElementById('upload-area');
		this.fileInput = document.getElementById('file-input');
		this.uploadBtn = document.getElementById('upload-btn');
		this.uploadStatus = document.getElementById('upload-status');
	}

	attachEventListeners() {
		// Chat functionality
		this.sendBtn.addEventListener('click', () => this.sendMessage());
		this.messageInput.addEventListener('keypress', (e) => {
			if (e.key === 'Enter' && !e.shiftKey) {
				e.preventDefault();
				this.sendMessage();
			}
		});

		// File upload functionality
		this.uploadArea.addEventListener('click', () => this.fileInput.click());
		this.uploadArea.addEventListener('dragover', (e) => {
			e.preventDefault();
			this.uploadArea.classList.add('dragover');
		});
		this.uploadArea.addEventListener('dragleave', () => {
			this.uploadArea.classList.remove('dragover');
		});
		this.uploadArea.addEventListener('drop', (e) => {
			e.preventDefault();
			this.uploadArea.classList.remove('dragover');
			this.handleFiles(e.dataTransfer.files);
		});

		this.fileInput.addEventListener('change', (e) => {
			this.handleFiles(e.target.files);
		});

		this.uploadBtn.addEventListener('click', () => this.uploadDocuments());
	}

	async checkConnection() {
		try {
			const response = await fetch(`${this.baseUrl}/health`);
			if (response.ok) {
				const data = await response.json();
				this.isConnected = true;
				this.connectionStatus.textContent = 'Connected';

				// Update health indicator
				const healthPercent = Object.values(data.services).every((s) => s) ? 100 : 50;
				document.getElementById('system-health').style.width = `${healthPercent}%`;
				document.getElementById('health-status').textContent = data.status;

				// Load stats immediately when connection is established
				this.loadStats();
			} else {
				throw new Error('Server not responding');
			}
		} catch (error) {
			this.isConnected = false;
			this.connectionStatus.textContent = 'Disconnected';
			document.getElementById('health-status').textContent = 'Offline';
			this.showNotification('Connection failed. Please ensure the server is running.', 'error');
		}
	}

	async loadStats() {
		if (!this.isConnected) return;

		try {
			// Show loading state
			document.getElementById('total-queries').textContent = '...';
			document.getElementById('active-docs').textContent = '...';
			document.getElementById('cache-hit').textContent = '...';

			const response = await fetch(`${this.baseUrl}/stats`);
			if (response.ok) {
				const stats = await response.json();

				document.getElementById('total-queries').textContent = stats.total_queries || 0;
				document.getElementById('active-docs').textContent = stats.active_documents || 0;
				document.getElementById('cache-hit').textContent = stats.cache_hit_rate
					? `${Math.round(stats.cache_hit_rate)}%`
					: '0%';
			} else {
				// Show error state
				document.getElementById('total-queries').textContent = '-';
				document.getElementById('active-docs').textContent = '-';
				document.getElementById('cache-hit').textContent = '-';
			}
		} catch (error) {
			console.error('Failed to load stats:', error);
			// Show error state
			document.getElementById('total-queries').textContent = '-';
			document.getElementById('active-docs').textContent = '-';
			document.getElementById('cache-hit').textContent = '-';
		}
	}

	addMessage(content, isUser = false, metadata = {}) {
		const messageDiv = document.createElement('div');
		messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

		let html = `<div>${content}</div>`;

		if (!isUser && metadata.sources && metadata.sources.length > 0) {
			html += `<div class="sources">
                        <strong>Sources:</strong>
                        ${metadata.sources.map((source) => `<span class="source-item">${source.title}</span>`).join('')}
                        <button class="download-sources-btn" onclick="chatbot.downloadSources(${JSON.stringify(
													metadata.sources
												).replace(/"/g, '&quot;')})">
                            <svg class="icon"><use href="#i-download" /></svg>
                            Download Sources
                        </button>
                    </div>`;
		}

		if (metadata.confidence) {
			html += `<div class="message-meta">Confidence: ${Math.round(metadata.confidence * 100)}%</div>`;
		}

		messageDiv.innerHTML = html;
		this.chatMessages.appendChild(messageDiv);
		this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
	}

	async sendMessage() {
		const message = this.messageInput.value.trim();
		if (!message || !this.isConnected) return;

		// Add user message
		this.addMessage(message, true);
		this.messageInput.value = '';

		// Disable input while processing
		this.sendBtn.disabled = true;
		const sendBtnContent = this.sendBtn.innerHTML;
		this.sendBtn.innerHTML = '<div class="loading"></div>';

		try {
			const response = await fetch(`${this.baseUrl}/chat`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					message: message,
					conversation_id: this.conversationId,
					context_window: 5,
				}),
			});

			if (response.ok) {
				const data = await response.json();
				this.addMessage(data.answer, false, {
					sources: data.sources,
					confidence: data.confidence,
					responseTime: data.response_time_ms,
				});

				// Refresh stats after successful query
				this.loadStats();
			} else {
				throw new Error(`HTTP ${response.status}`);
			}
		} catch (error) {
			this.addMessage('Sorry, I encountered an error processing your request. Please try again.', false);
			this.showNotification('Failed to send message', 'error');
		} finally {
			// Re-enable input
			this.sendBtn.disabled = false;
			this.sendBtn.innerHTML = sendBtnContent;
			this.messageInput.focus();
		}
	}

	handleFiles(files) {
		this.selectedFiles = Array.from(files).filter((file) => {
			const validTypes = ['text/plain', 'text/markdown', 'application/json', 'application/pdf'];
			const validExtensions = ['.txt', '.md', '.json', '.pdf'];
			const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
			return validTypes.includes(file.type) || validExtensions.includes(fileExtension);
		});

		if (this.selectedFiles.length === 0) {
			this.showNotification('Please select valid text, markdown, JSON, or PDF files', 'error');
			return;
		}

		this.uploadBtn.disabled = false;
		this.uploadStatus.innerHTML = `${this.selectedFiles.length} file(s) selected`;
	}

	async uploadDocuments() {
		if (this.selectedFiles.length === 0) return;

		this.uploadBtn.disabled = true;
		this.uploadBtn.innerHTML = '<div class="loading"></div>';
		this.uploadStatus.innerHTML = 'Processing files...';

		try {
			const documents = [];

			// Read each file
			for (const file of this.selectedFiles) {
				let content;
				const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');

				if (isPdf) {
					// For PDF files, send as base64
					content = await this.readFileAsBase64(file);
				} else {
					// For text files, read as text
					content = await this.readFileAsText(file);
				}

				documents.push({
					id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
					title: file.name.replace(/\.[^/.]+$/, ''),
					content: content,
					metadata: {
						filename: file.name,
						file_size: file.size,
						file_type: file.type,
						upload_time: new Date().toISOString(),
						is_pdf: isPdf,
					},
				});
			}

			const response = await fetch(`${this.baseUrl}/documents/upload`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					documents: documents,
					collection_name: 'web_upload',
				}),
			});

			if (response.ok) {
				const result = await response.json();
				this.showNotification(`Successfully uploaded ${result.processed} document(s)`, 'success');
				this.uploadStatus.innerHTML = `Uploaded ${result.processed} document(s)`;
				this.selectedFiles = [];
				this.fileInput.value = '';
				this.loadStats(); // Refresh stats
			} else {
				throw new Error(`HTTP ${response.status}`);
			}
		} catch (error) {
			this.showNotification('Failed to upload documents', 'error');
			this.uploadStatus.innerHTML = 'Upload failed';
		} finally {
			this.uploadBtn.disabled = true;
			this.uploadBtn.textContent = 'Upload Documents';
		}
	}

	readFileAsText(file) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = (e) => resolve(e.target.result);
			reader.onerror = (e) => reject(e);
			reader.readAsText(file);
		});
	}

	readFileAsBase64(file) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = (e) => {
				// Remove the data:application/pdf;base64, prefix
				const base64 = e.target.result.split(',')[1];
				resolve(base64);
			};
			reader.onerror = (e) => reject(e);
			reader.readAsDataURL(file);
		});
	}

	downloadSources(sources) {
		try {
			// Create a formatted text file with source information
			let content = 'CHATBOT SOURCES\n';
			content += '================\n';
			content += `Downloaded: ${new Date().toISOString()}\n\n`;

			sources.forEach((source, index) => {
				content += `SOURCE ${index + 1}\n`;
				content += `-----------\n`;
				content += `Title: ${source.title}\n`;
				content += `ID: ${source.id}\n`;
				content += `Relevance Score: ${source.score.toFixed(3)}\n`;
				content += `Content:\n${source.content}\n`;

				if (source.metadata) {
					content += `\nMetadata:\n`;
					Object.entries(source.metadata).forEach(([key, value]) => {
						content += `  ${key}: ${value}\n`;
					});
				}

				content += `\n${'='.repeat(50)}\n\n`;
			});

			// Create and download the file
			const blob = new Blob([content], { type: 'text/plain' });
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.style.display = 'none';
			a.href = url;
			a.download = `chatbot-sources-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);

			this.showNotification('Sources downloaded successfully!', 'success');
		} catch (error) {
			console.error('Error downloading sources:', error);
			this.showNotification('Failed to download sources', 'error');
		}
	}

	showNotification(message, type = 'success') {
		const notification = document.createElement('div');
		notification.className = `notification ${type}`;
		notification.textContent = message;
		document.body.appendChild(notification);

		// Show notification
		setTimeout(() => notification.classList.add('show'), 100);

		// Hide and remove after 3 seconds
		setTimeout(() => {
			notification.classList.remove('show');
			setTimeout(() => document.body.removeChild(notification), 300);
		}, 3000);
	}
}

// Initialize the chatbot when page loads
let chatbot;
document.addEventListener('DOMContentLoaded', () => {
	chatbot = new AcademicChatBot();
});
