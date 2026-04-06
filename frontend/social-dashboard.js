/**
 * Sosyal Medya Dashboard JavaScript
 */

class SocialMediaDashboard {
    constructor() {
        this.selectedVideo = null;
        this.platformStatus = {};
        this.shareHistory = [];
        this.init();
    }

    init() {
        this.loadVideos();
        this.checkPlatformStatus();
        this.loadShareHistory();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Video seçimi
        document.addEventListener('click', (e) => {
            if (e.target.closest('.video-item')) {
                this.selectVideo(e.target.closest('.video-item'));
            }
        });
    }

    async loadVideos() {
        try {
            const response = await fetch('/api/videos');
            const videos = await response.json();
            
            const videoGrid = document.getElementById('video-grid');
            videoGrid.innerHTML = '';
            
            videos.forEach(video => {
                if (video.status === 'completed') {
                    const videoItem = this.createVideoItem(video);
                    videoGrid.appendChild(videoItem);
                }
            });
        } catch (error) {
            console.error('Videolar yüklenirken hata:', error);
        }
    }

    createVideoItem(video) {
        const div = document.createElement('div');
        div.className = 'video-item';
        div.dataset.videoId = video.id;
        
        div.innerHTML = `
            <video class="video-thumbnail" controls>
                <source src="/videos/${video.filename}" type="video/mp4">
            </video>
            <div class="video-info">
                <div class="video-title">${video.topic}</div>
                <div class="video-duration">${video.duration}s</div>
            </div>
        `;
        
        return div;
    }

    selectVideo(videoElement) {
        // Önceki seçimi temizle
        document.querySelectorAll('.video-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Yeni seçimi işaretle
        videoElement.classList.add('selected');
        
        // Video bilgilerini form'a doldur
        const videoId = videoElement.dataset.videoId;
        this.selectedVideo = videoId;
        
        // Video başlığını otomatik doldur
        const title = videoElement.querySelector('.video-title').textContent;
        document.getElementById('video-title').value = title;
        
        // Etiketleri otomatik oluştur
        const tags = this.generateTagsFromTitle(title);
        document.getElementById('video-tags').value = tags.join(', ');
        
        // Açıklama oluştur
        const description = this.generateDescription(title);
        document.getElementById('video-description').value = description;
    }

    generateTagsFromTitle(title) {
        // Başlıktan etiketler oluştur
        const words = title.toLowerCase().split(' ');
        const tags = [];
        
        words.forEach(word => {
            if (word.length > 3 && !tags.includes(word)) {
                tags.push(word);
            }
        });
        
        // Varsayılan etiketler
        tags.push('teknoloji', 'AI', 'video');
        
        return tags.slice(0, 8); // Maksimum 8 etiket
    }

    generateDescription(title) {
        return `${title} hakkında detaylı bir video. Bu video AI Video Bot tarafından otomatik olarak üretilmiştir. İçerikteki bilgiler doğruluğu kontrol edilmiş ve size sunulmuştur.

🎬 AI Video Bot ile otomatik video üretimi
🔥 Daha fazlası için kanalımıza abone olun!

#AI #Video #Teknoloji`;
    }

    async checkPlatformStatus() {
        try {
            const response = await fetch('/api/social/status');
            const status = await response.json();
            
            this.updatePlatformStatus(status);
        } catch (error) {
            console.error('Platform durumu kontrol edilemedi:', error);
        }
    }

    updatePlatformStatus(status) {
        Object.keys(status).forEach(platform => {
            const statusElement = document.getElementById(`${platform}-status`);
            const platformCard = document.querySelector(`[data-platform="${platform}"]`);
            
            if (statusElement) {
                statusElement.textContent = status[platform] ? 'Bağlı' : 'Bağlı Değil';
                statusElement.className = `status-badge ${status[platform] ? 'connected' : 'disconnected'}`;
            }
            
            if (platformCard && status[platform]) {
                platformCard.classList.add('connected');
            }
        });
    }

    async loadShareHistory() {
        try {
            const response = await fetch('/api/social/history');
            const history = await response.json();
            
            this.shareHistory = history;
            this.renderShareHistory();
        } catch (error) {
            console.error('Paylaşım geçmişi yüklenemedi:', error);
        }
    }

    renderShareHistory() {
        const tbody = document.getElementById('history-tbody');
        tbody.innerHTML = '';
        
        this.shareHistory.forEach(share => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${share.video_title}</td>
                <td>${share.platforms.join(', ')}</td>
                <td>
                    <span class="status-badge ${share.success ? 'connected' : 'disconnected'}">
                        ${share.success ? 'Başarılı' : 'Başarısız'}
                    </span>
                </td>
                <td>${new Date(share.created_at).toLocaleString('tr-TR')}</td>
                <td>
                    ${share.success ? 
                        `<a href="${share.post_url}" target="_blank" class="btn btn-sm">Görüntüle</a>` : 
                        `<span class="text-danger">${share.error}</span>`
                    }
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    async shareVideo() {
        if (!this.selectedVideo) {
            alert('Lütfen bir video seçin!');
            return;
        }

        const title = document.getElementById('video-title').value;
        const description = document.getElementById('video-description').value;
        const tags = document.getElementById('video-tags').value.split(',').map(tag => tag.trim());
        const scheduleTime = document.getElementById('schedule-time').value;
        
        // Seçili platformları al
        const platforms = [];
        document.querySelectorAll('.platform-checkboxes input:checked').forEach(checkbox => {
            platforms.push(checkbox.value);
        });

        if (platforms.length === 0) {
            alert('Lütfen en az bir platform seçin!');
            return;
        }

        const shareData = {
            video_id: this.selectedVideo,
            title: title,
            description: description,
            tags: tags,
            platforms: platforms,
            schedule_time: scheduleTime
        };

        try {
            const response = await fetch('/api/social/share', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shareData)
            });

            const result = await response.json();

            if (response.ok) {
                alert('Video paylaşım için kuyruğa alındı!');
                this.loadShareHistory();
            } else {
                alert('Paylaşım hatası: ' + result.error);
            }
        } catch (error) {
            console.error('Paylaşım hatası:', error);
            alert('Paylaşım sırasında bir hata oluştu!');
        }
    }

    previewContent() {
        const title = document.getElementById('video-title').value;
        const description = document.getElementById('video-description').value;
        const tags = document.getElementById('video-tags').value.split(',').map(tag => tag.trim());
        
        // Preview modal oluştur
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>İçerik Önizlemesi</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <span class="material-symbols-rounded">close</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="preview-section">
                        <h4>YouTube</h4>
                        <p><strong>Başlık:</strong> ${title}</p>
                        <p><strong>Açıklama:</strong> ${description}</p>
                        <p><strong>Etiketler:</strong> ${tags.join(', ')}</p>
                    </div>
                    <div class="preview-section">
                        <h4>Twitter</h4>
                        <p>${title.substring(0, 200)}...</p>
                        <p>${tags.map(tag => '#' + tag).join(' ')}</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Kapat</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
}

// Global functions
function showConfigModal() {
    document.getElementById('config-modal').style.display = 'block';
}

function closeConfigModal() {
    document.getElementById('config-modal').style.display = 'none';
}

function showTab(platform) {
    // Tab butonlarını güncelle
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Tab content'ını güncelle
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(`${platform}-tab`).classList.add('active');
}

function connectPlatform(platform) {
    alert(`${platform.toUpperCase()} platformuna bağlanmak için API ayarlarını yapın!`);
    showConfigModal();
}

function backToDashboard() {
    window.location.href = '/';
}

function saveConfig() {
    // Konfigürasyonu kaydet
    const config = {
        youtube: {
            api_key: document.getElementById('youtube-api-key').value,
            category: document.getElementById('youtube-category').value
        },
        twitter: {
            api_key: document.getElementById('twitter-api-key').value,
            api_secret: document.getElementById('twitter-api-secret').value,
            access_token: document.getElementById('twitter-access-token').value,
            access_token_secret: document.getElementById('twitter-access-token-secret').value
        },
        tiktok: {
            session_id: document.getElementById('tiktok-session-id').value,
            username: document.getElementById('tiktok-username').value
        },
        facebook: {
            page_id: document.getElementById('facebook-page-id').value,
            access_token: document.getElementById('facebook-access-token').value
        }
    };

    fetch('/api/social/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Konfigürasyon kaydedildi!');
            closeConfigModal();
            location.reload();
        } else {
            alert('Hata: ' + result.error);
        }
    })
    .catch(error => {
        console.error('Konfigürasyon hatası:', error);
        alert('Konfigürasyon kaydedilemedi!');
    });
}

// Initialize
let socialDashboard;

document.addEventListener('DOMContentLoaded', () => {
    socialDashboard = new SocialMediaDashboard();
});

// Export functions for global access
window.shareVideo = () => socialDashboard.shareVideo();
window.previewContent = () => socialDashboard.previewContent();
