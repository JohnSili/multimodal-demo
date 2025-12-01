const API_BASE = window.location.origin;

let currentSessionId = localStorage.getItem('session_id') || null;
let currentImageBase64 = null;
let currentOcrTaskId = null;

document.getElementById('tab-vqa').addEventListener('click', () => switchTab('vqa'));
document.getElementById('tab-ocr').addEventListener('click', () => switchTab('ocr'));

function switchTab(tab) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`content-${tab}`).classList.remove('hidden');
    
    lucide.createIcons();
}
const dropZone = document.getElementById('drop-zone');
const imageInput = document.getElementById('image-input');
const imagePreview = document.getElementById('image-preview');
const previewImg = document.getElementById('preview-img');
const questionSection = document.getElementById('question-section');
const questionInput = document.getElementById('question-input');
const askButton = document.getElementById('ask-button');
const clearImage = document.getElementById('clear-image');
const clearSession = document.getElementById('clear-session');
const chatHistory = document.getElementById('chat-history');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drop-zone-active');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drop-zone-active');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drop-zone-active');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleImageFile(files[0]);
    }
});

dropZone.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleImageFile(e.target.files[0]);
    }
});

function handleImageFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Неподдерживаемый формат файла. Используйте JPEG, PNG или WebP.');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showError('Размер файла превышает 10MB.');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        currentImageBase64 = e.target.result.split(',')[1];
        previewImg.src = e.target.result;
        imagePreview.classList.remove('hidden');
        questionSection.classList.remove('hidden');
        dropZone.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

clearImage.addEventListener('click', () => {
    currentImageBase64 = null;
    currentSessionId = null;
    imagePreview.classList.add('hidden');
    questionSection.classList.add('hidden');
    dropZone.classList.remove('hidden');
    chatHistory.innerHTML = '<p class="text-gray-500 text-center py-8">Загрузите изображение, чтобы начать</p>';
    localStorage.removeItem('session_id');
});

clearSession.addEventListener('click', () => {
    currentSessionId = null;
    localStorage.removeItem('session_id');
    chatHistory.innerHTML = '<p class="text-gray-500 text-center py-8">Сессия очищена</p>';
    showSuccess('Сессия очищена');
});

askButton.addEventListener('click', async () => {
    if (!currentImageBase64) {
        showError('Пожалуйста, загрузите изображение');
        return;
    }
    
    const question = questionInput.value.trim();
    
    addMessageToChat('user', question || 'Автоматическое описание');
    
    askButton.disabled = true;
    askButton.innerHTML = '<span class="spinner"></span> Обработка...';
    
    try {
        const response = await fetch(`${API_BASE}/api/vqa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: currentImageBase64,
                question: question || null,
                session_id: currentSessionId
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail?.message || data.detail || 'Ошибка при обработке запроса');
        }
        
        currentSessionId = data.session_id;
        localStorage.setItem('session_id', currentSessionId);
        
        addMessageToChat('assistant', data.answer);
        
        questionInput.value = '';
        
    } catch (error) {
        showError(error.message);
        addMessageToChat('error', error.message);
    } finally {
        askButton.disabled = false;
        askButton.innerHTML = '<i data-lucide="send" class="w-4 h-4 mr-2"></i>Отправить вопрос';
        lucide.createIcons();
    }
});

function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message mb-4';
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <i data-lucide="user" class="w-4 h-4 text-white"></i>
                </div>
                <div class="flex-1 bg-blue-100 rounded-lg p-3">
                    <p class="text-gray-800">${escapeHtml(content)}</p>
                </div>
            </div>
        `;
    } else if (role === 'assistant') {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <i data-lucide="bot" class="w-4 h-4 text-white"></i>
                </div>
                <div class="flex-1 bg-white rounded-lg p-3 border border-gray-200">
                    <p class="text-gray-800 whitespace-pre-wrap">${escapeHtml(content)}</p>
                </div>
            </div>
        `;
    } else if (role === 'error') {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                    <i data-lucide="alert-circle" class="w-4 h-4 text-white"></i>
                </div>
                <div class="flex-1 bg-red-100 rounded-lg p-3 border border-red-300">
                    <p class="text-red-800">${escapeHtml(content)}</p>
                </div>
            </div>
        `;
    }
    
    if (chatHistory.querySelector('p.text-gray-500')) {
        chatHistory.innerHTML = '';
    }
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    lucide.createIcons();
}

const dropZoneOcr = document.getElementById('drop-zone-ocr');
const imageInputOcr = document.getElementById('image-input-ocr');
const imagePreviewOcr = document.getElementById('image-preview-ocr');
const previewImgOcr = document.getElementById('preview-img-ocr');
const ocrButton = document.getElementById('ocr-button');
const clearImageOcr = document.getElementById('clear-image-ocr');
const languageSelect = document.getElementById('language-select');
const ocrResult = document.getElementById('ocr-result');
const downloadOcr = document.getElementById('download-ocr');

let currentOcrImageBase64 = null;

dropZoneOcr.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZoneOcr.classList.add('drop-zone-active');
});

dropZoneOcr.addEventListener('dragleave', () => {
    dropZoneOcr.classList.remove('drop-zone-active');
});

dropZoneOcr.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZoneOcr.classList.remove('drop-zone-active');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleOcrImageFile(files[0]);
    }
});

dropZoneOcr.addEventListener('click', () => imageInputOcr.click());
imageInputOcr.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleOcrImageFile(e.target.files[0]);
    }
});

function handleOcrImageFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Неподдерживаемый формат файла. Используйте JPEG, PNG или WebP.');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showError('Размер файла превышает 10MB.');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        currentOcrImageBase64 = e.target.result.split(',')[1];
        previewImgOcr.src = e.target.result;
        imagePreviewOcr.classList.remove('hidden');
        dropZoneOcr.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

clearImageOcr.addEventListener('click', () => {
    currentOcrImageBase64 = null;
    currentOcrTaskId = null;
    imagePreviewOcr.classList.add('hidden');
    dropZoneOcr.classList.remove('hidden');
    ocrResult.innerHTML = '<p class="text-gray-500 text-center py-8">Загрузите изображение и нажмите "Распознать текст"</p>';
    downloadOcr.classList.add('hidden');
});

ocrButton.addEventListener('click', async () => {
    if (!currentOcrImageBase64) {
        showError('Пожалуйста, загрузите изображение');
        return;
    }
    
    ocrButton.disabled = true;
    ocrButton.innerHTML = '<span class="spinner"></span> Распознавание...';
    ocrResult.innerHTML = '<div class="text-center py-8"><span class="spinner"></span><p class="mt-4 text-gray-600">Обработка изображения...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/ocr`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: currentOcrImageBase64,
                language: languageSelect.value
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail?.message || data.detail || 'Ошибка при распознавании текста');
        }
        
        ocrResult.innerHTML = `
            <div class="bg-white rounded-lg p-4 border border-gray-200">
                <pre class="whitespace-pre-wrap text-sm text-gray-800 font-mono">${escapeHtml(data.text)}</pre>
            </div>
        `;
        
        currentOcrTaskId = data.task_id;
        downloadOcr.classList.remove('hidden');
        
        showSuccess('Текст успешно распознан');
        
    } catch (error) {
        showError(error.message);
        ocrResult.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <p class="text-red-800">${escapeHtml(error.message)}</p>
            </div>
        `;
    } finally {
        ocrButton.disabled = false;
        ocrButton.innerHTML = '<i data-lucide="scan" class="w-4 h-4 mr-2"></i>Распознать текст';
        lucide.createIcons();
    }
});

downloadOcr.addEventListener('click', async () => {
    if (!currentOcrTaskId) {
        showError('Нет результата для скачивания');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/download/ocr/${currentOcrTaskId}`);
        if (!response.ok) {
            throw new Error('Ошибка при скачивании файла');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ocr_result_${currentOcrTaskId}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showSuccess('Файл успешно скачан');
    } catch (error) {
        showError(error.message);
    }
});

function showError(message) {
    showToast(message, 'error');
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast bg-white rounded-lg shadow-lg p-4 flex items-center space-x-3 min-w-80 max-w-md`;
    
    const icon = type === 'error' ? 'alert-circle' : 'check-circle';
    const color = type === 'error' ? 'text-red-500' : 'text-green-500';
    const bgColor = type === 'error' ? 'bg-red-50' : 'bg-green-50';
    
    toast.classList.add(bgColor);
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 ${color}"></i>
        <p class="flex-1 text-gray-800">${escapeHtml(message)}</p>
        <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;
    
    const container = document.getElementById('toast-container');
    container.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

lucide.createIcons();

