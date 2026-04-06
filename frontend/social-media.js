/**
 * Sosyal Medya Paylaşım Arayüzü
 */

class SocialMediaManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPlatformStatus();
        this.loadPostsHistory();
    }

    setupEventListeners() {
        // Platform bağlantı butonları
        document.querySelectorAll('.connect-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const platform = e.target.closest('.platform-card').dataset.platform;
                this.connectPlatform(platform);
            });
        });

        // Platform test butonları
        document.querySelectorAll('.test-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const platform = e.target.closest('.platform-card').dataset.platform;
                this.testPlatform(platform);
            });
        });

        // Hemen paylaşım butonu
        const postNowBtn = document.getElementById('post-now-btn');
        if (postNowBtn) {
            postNowBtn.addEventListener('click', () => {
                this.postNow();
            });
        }

        // Zamanlanmış paylaşım butonu
        const scheduleBtn = document.getElementById('schedule-btn');
        if (scheduleBtn) {
            scheduleBtn.addEventListener('click', () => {
                this.schedulePost();
            });
        }

        // Video seçimi
        const videoSelect = document.getElementById('video-select');
        if (videoSelect) {
            videoSelect.addEventListener('change', () => {
                this.updateContentPreview();
            });
        }
    }

    async loadPlatformStatus() {
        try {
            const response = await fetch('/api/social/platforms');
            const platforms = await response.json();
            
            this.updatePlatformUI(platforms);
        } catch (error) {
            console.error('Platform durumu yüklenemedi:', error);
        }
    }

    async loadPostsHistory() {
        try {
            const response = await fetch('/api/social/posts');
            const posts = await response.json();
            
            this.updatePostsHistory(posts);
        } catch (error) {
            console.error('Gönderi geçmişi yüklenemedi:', error);
        }
    }

    updatePlatformUI(platforms) {
        Object.keys(platforms).forEach(platform => {
            const card = document.querySelector(`[data-platform="${platform}"]`);
            if (!card) return;

            const statusDot = card.querySelector('.status-dot');
            const statusText = card.querySelector('.platform-status');
            const connectBtn = card.querySelector('.connect-btn');

            if (platforms[platform].connected) {
                statusDot.classList.add('connected');
                statusText.textContent = 'Bağlı';
                card.classList.add('connected');
                connectBtn.textContent = 'Bağlantıyı Kes';
                connectBtn.classList.remove('connect-btn');
                connectBtn.classList.add('disconnect-btn');
            } else {
                statusDot.classList.remove('connected');
                statusText.textContent = 'Bağlı Değil';
                card.classList.remove('connected');
                connectBtn.textContent = 'Bağlan';
                connectBtn.classList.remove('disconnect-btn');
                connectBtn.classList.add('connect-btn');
            }
        });
    }

    updatePostsHistory(posts) {
        const historyContainer = document.getElementById('posts-history');
        if (!historyContainer) return;

        if (posts.length === 0) {
            historyContainer.innerHTML = '<p class="text-muted">Henüz gönderi yapılmadı.</p>';
            return;
        }

        const postsHTML = posts.map(post => `
            <div class="post-item">
                <div class="post-platform ${post.platform}-icon">
                    ${this.getPlatformIcon(post.platform)}
                </div>
                <div class="post-info">
                    <div class="post-title">${post.title}</div>
                    <div class="post-meta">
                        ${post.platform} • ${new Date(post.created_at).toLocaleString('tr-TR')}
                    </div>
                </div>
                <div class="post-status status-${post.status}">
                    ${this.getStatusText(post.status)}
                </div>
            </div>
        `).join('');

        historyContainer.innerHTML = postsHTML;
    }

    getPlatformIcon(platform) {
        const icons = {
            'youtube': '<i class="fab fa-youtube"></i>',
            'twitter': '<i class="fab fa-twitter"></i>',
            'tiktok': '<i class="fab fa-tiktok"></i>',
            'facebook': '<i class="fab fa-facebook"></i>'
        };
        return icons[platform] || '';
    }

    getStatusText(status) {
        const statusTexts = {
            'pending': 'Bekliyor',
            'posted': 'Yayınlandı',
            'failed': 'Başarısız'
        };
        return statusTexts[status] || status;
    }

    async connectPlatform(platform) {
        try {
            showNotification(`${platform} bağlanıyor...`, 'info');
            
            const response = await fetch(`/api/social/connect/${platform}`, {
                method: 'POST'
            });

            if (response.ok) {
                showNotification(`${platform} başarıyla bağlandı!`, 'success');
                this.loadPlatformStatus();
            } else {
                const error = await response.json();
                showNotification(`Bağlantı hatası: ${error.message}`, 'error');
            }
        } catch (error) {
            console.error('Platform bağlantı hatası:', error);
            showNotification('Bağlantı hatası oluştu', 'error');
        }
    }

    async testPlatform(platform) {
        try {
            showNotification(`${platform} test ediliyor...`, 'info');
            
            const response = await fetch(`/api/social/test/${platform}`, {
                method: 'POST'
            });

            if (response.ok) {
                showNotification(`${platform} test başarılı!`, 'success');
            } else {
                const error = await response.json();
                showNotification(`Test hatası: ${error.message}`, 'error');
            }
        } catch (error) {
            console.error('Platform test hatası:', error);
            showNotification('Test hatası oluştu', 'error');
        }
    }

    async updateContentPreview() {
        const videoSelect = document.getElementById('video-select');
        const selectedOption = videoSelect.options[videoSelect.selectedIndex];
        
        if (!selectedOption) return;

        const videoData = {
            title: selectedOption.textContent,
            topic: selectedOption.dataset.topic,
            description: selectedOption.dataset.description
        };

        try {
            const response = await fetch('/api/social/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(videoData)
            });

            if (response.ok) {
                const preview = await response.json();
                this.displayContentPreview(preview);
            }
        } catch (error) {
            console.error('İçerik önizleme hatası:', error);
        }
    }

    displayContentPreview(preview) {
        // YouTube önizlemesi
        const youtubePreview = document.getElementById('youtube-preview');
        if (youtubePreview) {
            youtubePreview.innerHTML = `
                <div class="preview-title">${preview.youtube.title}</div>
                <div class="preview-description">${preview.youtube.description}</div>
                <div class="preview-tags">${preview.youtube.tags}</div>
            `;
        }

        // Twitter önizlemesi
        const twitterPreview = document.getElementById('twitter-preview');
        if (twitterPreview) {
            twitterPreview.innerHTML = `
                <div class="preview-description">${preview.twitter.text}</div>
            `;
        }

        // TikTok önizlemesi
        const tiktokPreview = document.getElementById('tiktok-preview');
        if (tiktokPreview) {
            tiktokPreview.innerHTML = `
                <div class="preview-description">${preview.tiktok.text}</div>
            `;
        }

        // Facebook önizlemesi
        const facebookPreview = document.getElementById('facebook-preview');
        if (facebookPreview) {
            facebookPreview.innerHTML = `
                <div class="preview-description">${preview.facebook.text}</div>
            `;
        }
    }

    async postNow() {
        const selectedPlatforms = this.getSelectedPlatforms();
        const videoId = document.getElementById('video-select').value;

        if (selectedPlatforms.length === 0) {
            showNotification('Lütfen en az bir platform seçin', 'error');
            return;
        }

        if (!videoId) {
            showNotification('Lütfen bir video seçin', 'error');
            return;
        }

        try {
            showNotification('Gönderi paylaşılıyor...', 'info');

            const response = await fetch('/api/social/post', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    video_id: videoId,
                    platforms: selectedPlatforms,
                    schedule_time: null
                })
            });

            if (response.ok) {
                showNotification('Gönderi başarıyla paylaşıldı!', 'success');
                this.loadPostsHistory();
            } else {
                const error = await response.json();
                showNotification(`Paylaşım hatası: ${error.message}`, 'error');
            }
        } catch (error) {
            console.error('Paylaşım hatası:', error);
            showNotification('Paylaşım hatası oluştu', 'error');
        }
    }

    async schedulePost() {
        const selectedPlatforms = this.getSelectedPlatforms();
        const videoId = document.getElementById('video-select').value;
        const scheduleDate = document.getElementById('schedule-date').value;
        const scheduleTime = document.getElementById('schedule-time').value;

        if (selectedPlatforms.length === 0) {
            showNotification('Lütfen en az bir platform seçin', 'error');
            return;
        }

        if (!videoId) {
            showNotification('Lütfen bir video seçin', 'error');
            return;
        }

        if (!scheduleDate || !scheduleTime) {
            showNotification('Lütfen paylaşım zamanını seçin', 'error');
            return;
        }

        const scheduleDateTime = new Date(`${scheduleDate}T${scheduleTime}`);
        
        try {
            showNotification('Gönderi zamanlanıyor...', 'info');

            const response = await fetch('/api/social/post', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    video_id: videoId,
                    platforms: selectedPlatforms,
                    schedule_time: scheduleDateTime.toISOString()
                })
            });

            if (response.ok) {
                showNotification('Gönderi başarıyla zamanlandı!', 'success');
                this.loadPostsHistory();
            } else {
                const error = await response.json();
                showNotification(`Zamanlama hatası: ${error.message}`, 'error');
            }
        } catch (error) {
            console.error('Zamanlama hatası:', error);
            showNotification('Zamanlama hatası oluştu', 'error');
        }
    }

    getSelectedPlatforms() {
        const checkboxes = document.querySelectorAll('.platform-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
}

// Global instance
let socialMediaManager;

// DOM hazır olduğunda başlat
document.addEventListener('DOMContentLoaded', () => {
    socialMediaManager = new SocialMediaManager();
});
