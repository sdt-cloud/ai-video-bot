/**
 * Nedir.me Entegrasyonu için Frontend Modülü
 */

class NedirIntegration {
    constructor() {
        this.apiBase = '/api/nedir';
        this.init();
    }

    init() {
        this.addNedirSection();
        this.bindEvents();
    }

    addNedirSection() {
        const nav = document.querySelector('nav ul');
        if (!nav) return;

        const nedirNavItem = document.createElement('li');
        nedirNavItem.innerHTML = `
            <a href="#nedir" data-section="nedir">
                <i class="fas fa-book"></i>
                <span>Nedir.me</span>
            </a>
        `;
        nav.appendChild(nedirNavItem);

        // Nedir.me section'ı ekle
        const sectionsContainer = document.querySelector('.sections');
        if (sectionsContainer) {
            sectionsContainer.insertAdjacentHTML('beforeend', `
                <div class="section" id="nedir-section" style="display: none;">
                    <div class="section-header">
                        <h2><i class="fas fa-book"></i> Nedir.me Entegrasyonu</h2>
                        <p>WordPress'ten kavramları alarak otomatik video üretimi</p>
                    </div>

                    <div class="nedir-controls">
                        <div class="control-group">
                            <label for="nedir-category">Kategori Filtresi:</label>
                            <select id="nedir-category">
                                <option value="">Tüm Kategoriler</option>
                                <option value="kavramlar">Kavramlar</option>
                                <option value="kimdir">Kimdir</option>
                                <option value="videolar">Videolar</option>
                                <option value="kisaltmalar">Kısaltmalar</option>
                                <option value="terimler">Terimler</option>
                                <option value="gunluk-dil">Günlük Dil</option>
                                <option value="yeni-kavramlar">Yeni Kavramlar</option>
                            </select>
                        </div>

                        <div class="control-group">
                            <label for="nedir-limit">Kavram Sayısı:</label>
                            <input type="number" id="nedir-limit" min="1" max="50" value="10">
                        </div>

                        <button id="fetch-concepts" class="btn btn-primary">
                            <i class="fas fa-download"></i> Kavramları Getir
                        </button>

                        <button id="bulk-create-videos" class="btn btn-success" style="display: none;">
                            <i class="fas fa-video"></i> Toplu Video Üret
                        </button>
                    </div>

                    <div id="concepts-container" style="display: none;">
                        <h3>Bulunan Kavramlar</h3>
                        <div id="concepts-list" class="concepts-grid"></div>
                    </div>

                    <div id="video-topics-container" style="display: none;">
                        <h3>Oluşturulacak Video Konuları</h3>
                        <div id="video-topics-list" class="topics-list"></div>
                    </div>
                </div>
            `);
        }
    }

    bindEvents() {
        // Navigation event
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-section="nedir"]')) {
                this.showSection('nedir');
            }
        });

        // Fetch concepts button
        const fetchBtn = document.getElementById('fetch-concepts');
        if (fetchBtn) {
            fetchBtn.addEventListener('click', () => this.fetchConcepts());
        }

        // Bulk create videos button
        const bulkBtn = document.getElementById('bulk-create-videos');
        if (bulkBtn) {
            bulkBtn.addEventListener('click', () => this.bulkCreateVideos());
        }

        // Category change event
        const categorySelect = document.getElementById('nedir-category');
        if (categorySelect) {
            categorySelect.addEventListener('change', () => this.clearResults());
        }
    }

    showSection(sectionName) {
        // Tüm section'ları gizle
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'none';
        });

        // Nav aktif durumunu güncelle
        document.querySelectorAll('nav a').forEach(link => {
            link.classList.remove('active');
        });

        // İlgili section'ı göster
        const section = document.getElementById(`${sectionName}-section`);
        if (section) {
            section.style.display = 'block';
        }

        // Nav link'ini aktif yap
        const navLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (navLink) {
            navLink.classList.add('active');
        }
    }

    async fetchConcepts() {
        const category = document.getElementById('nedir-category').value;
        const limit = document.getElementById('nedir-limit').value;

        this.showLoading('fetch-concepts');

        try {
            const response = await fetch(`${this.apiBase}/concepts?category=${category}&limit=${limit}`);
            const data = await response.json();

            if (data.status === 'success') {
                this.displayConcepts(data.data);
                this.generateVideoTopics(data.data);
            } else {
                this.showError('Kavramlar alınamadı: ' + data.message);
            }
        } catch (error) {
            this.showError('Bağlantı hatası: ' + error.message);
        } finally {
            this.hideLoading('fetch-concepts');
        }
    }

    displayConcepts(concepts) {
        const container = document.getElementById('concepts-container');
        const list = document.getElementById('concepts-list');

        if (!concepts || concepts.length === 0) {
            list.innerHTML = '<p class="no-results">Kavram bulunamadı.</p>';
            container.style.display = 'block';
            return;
        }

        list.innerHTML = concepts.map(concept => `
            <div class="concept-card">
                <h4>${this.escapeHtml(concept.title)}</h4>
                <p class="concept-category">${this.escapeHtml(concept.category)}</p>
                ${concept.description ? `<p class="concept-desc">${this.escapeHtml(concept.description.substring(0, 150))}...</p>` : ''}
                <div class="concept-actions">
                    <button class="btn btn-sm btn-primary" onclick="nedirIntegration.createSingleVideo('${this.escapeHtml(concept.title)}')">
                        <i class="fas fa-video"></i> Video Üret
                    </button>
                </div>
            </div>
        `).join('');

        container.style.display = 'block';
    }

    generateVideoTopics(concepts) {
        const topics = [];
        
        concepts.forEach(concept => {
            const title = concept.title;
            const category = concept.category;
            
            topics.push(`${title} nedir? ${category} kategorisinde açıklama`);
            
            if (concept.description && concept.description.length > 50) {
                topics.push(`${title}: ${concept.description.substring(0, 100)}...`);
            }
            
            topics.push(`${title} günlük hayatta nerelerde kullanılır?`);
        });

        this.displayVideoTopics(topics);
    }

    displayVideoTopics(topics) {
        const container = document.getElementById('video-topics-container');
        const list = document.getElementById('video-topics-list');
        const bulkBtn = document.getElementById('bulk-create-videos');

        list.innerHTML = topics.slice(0, 20).map((topic, index) => `
            <div class="topic-item">
                <span class="topic-number">${index + 1}</span>
                <span class="topic-text">${this.escapeHtml(topic)}</span>
                <button class="btn btn-sm btn-outline" onclick="nedirIntegration.removeTopic(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        container.style.display = 'block';
        bulkBtn.style.display = 'inline-block';
    }

    async bulkCreateVideos() {
        const category = document.getElementById('nedir-category').value;
        const limit = document.getElementById('nedir-limit').value;

        if (!confirm(`${limit} kavram için video üretimi başlatılsın mı? Bu işlem biraz zaman alabilir.`)) {
            return;
        }

        this.showLoading('bulk-create-videos');

        try {
            const response = await fetch(`${this.apiBase}/bulk-videos`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category: category,
                    max_concepts: parseInt(limit)
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.showSuccess(`${data.message}`);
                // Queue section'ına geç
                setTimeout(() => {
                    const queueLink = document.querySelector('[data-section="queue"]');
                    if (queueLink) {
                        queueLink.click();
                    }
                }, 1000);
            } else {
                this.showError('Video üretimi başlatılamadı: ' + data.message);
            }
        } catch (error) {
            this.showError('Bağlantı hatası: ' + error.message);
        } finally {
            this.hideLoading('bulk-create-videos');
        }
    }

    async createSingleVideo(topic) {
        try {
            const response = await fetch('/api/videos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    category: 'Nedir.me',
                    tone: 'Enerjik',
                    duration: 30,
                    language: 'tr'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Video kuyruğa eklendi!');
                // Queue section'ına geç
                setTimeout(() => {
                    const queueLink = document.querySelector('[data-section="queue"]');
                    if (queueLink) {
                        queueLink.click();
                    }
                }, 1000);
            } else {
                this.showError('Video eklenemedi: ' + data.error);
            }
        } catch (error) {
            this.showError('Bağlantı hatası: ' + error.message);
        }
    }

    removeTopic(button) {
        button.closest('.topic-item').remove();
    }

    clearResults() {
        document.getElementById('concepts-container').style.display = 'none';
        document.getElementById('video-topics-container').style.display = 'none';
        document.getElementById('bulk-create-videos').style.display = 'none';
    }

    showLoading(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> İşleniyor...';
        }
    }

    hideLoading(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = false;
            // Buton orijinal içeriğini geri yükle
            if (buttonId === 'fetch-concepts') {
                button.innerHTML = '<i class="fas fa-download"></i> Kavramları Getir';
            } else if (buttonId === 'bulk-create-videos') {
                button.innerHTML = '<i class="fas fa-video"></i> Toplu Video Üret';
            }
        }
    }

    showSuccess(message) {
        // App.js'teki mevcut showNotification fonksiyonunu kullan
        if (typeof showNotification === 'function') {
            showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    showError(message) {
        // App.js'teki mevcut showNotification fonksiyonunu kullan
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            alert(message);
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Global instance
let nedirIntegration;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    nedirIntegration = new NedirIntegration();
});
