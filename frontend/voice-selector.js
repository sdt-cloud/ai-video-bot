/**
 * Ses Seçici Arayüzü
 */

class VoiceSelector {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSavedVoiceType();
    }

    setupEventListeners() {
        // Ses tipi değiştiğinde
        document.addEventListener('voiceTypeChanged', (e) => {
            this.updateVoicePreview(e.detail.voiceType);
        });

        // Form submit edildiğinde
        const form = document.querySelector('#video-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                this.saveVoiceType();
            });
        }
    }

    loadSavedVoiceType() {
        const saved = localStorage.getItem('preferredVoiceType');
        if (saved) {
            const select = document.querySelector('#voice-type');
            if (select) {
                select.value = saved;
                this.updateVoicePreview(saved);
            }
        }
    }

    saveVoiceType() {
        const select = document.querySelector('#voice-type');
        if (select) {
            localStorage.setItem('preferredVoiceType', select.value);
        }
    }

    updateVoicePreview(voiceType) {
        const preview = document.querySelector('#voice-preview');
        if (!preview) return;

        const voiceDescriptions = {
            'erkek': 'Derin ve güçlü erkek sesi - Adam',
            'kadin': 'Net ve anlaşılır kadın sesi - Bella', 
            'cocuk': 'Neşeli ve enerjik çocuk sesi - Domi',
            'dramatik': 'Duygusal ve dramatik erkek sesi - Adam',
            'gulucu': 'Neşeli ve samimi kadın sesi - Bella',
            'profesyonel': 'Resmi ve profesyonel erkek sesi - Adam',
            'sakin': 'Sakin ve sıcak kadın sesi - Bella'
        };

        preview.innerHTML = `
            <div class="voice-preview-content">
                <div class="voice-icon">🎙️</div>
                <div class="voice-info">
                    <div class="voice-name">${this.getVoiceDisplayName(voiceType)}</div>
                    <div class="voice-desc">${voiceDescriptions[voiceType] || 'Standart ses'}</div>
                </div>
                <button class="test-voice-btn" onclick="voiceSelector.testVoice('${voiceType}')">
                    <i class="fas fa-play"></i> Test Et
                </button>
            </div>
        `;
    }

    getVoiceDisplayName(voiceType) {
        const names = {
            'erkek': 'Erkek Ses',
            'kadin': 'Kadın Ses',
            'cocuk': 'Çocuk Ses',
            'dramatik': 'Dramatik Ses',
            'gulucu': 'Gülücü Ses',
            'profesyonel': 'Profesyonel Ses',
            'sakin': 'Sakin Ses'
        };
        return names[voiceType] || 'Standart Ses';
    }

    async testVoice(voiceType) {
        const testText = "Bu bir test metnidir. Ses kalitesini kontrol etmek için kullanılır.";
        
        try {
            const response = await fetch('/api/test-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: testText,
                    voice_type: voiceType
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const audioUrl = URL.createObjectURL(blob);
                
                // Ses çalar
                const audio = new Audio(audioUrl);
                audio.play();
                
                // Buton durumunu güncelle
                const btn = document.querySelector('.test-voice-btn');
                if (btn) {
                    btn.innerHTML = '<i class="fas fa-check"></i> Test Ediliyor...';
                    btn.disabled = true;
                    
                    audio.addEventListener('ended', () => {
                        btn.innerHTML = '<i class="fas fa-check"></i> Test Edildi';
                        setTimeout(() => {
                            btn.innerHTML = '<i class="fas fa-play"></i> Test Et';
                            btn.disabled = false;
                        }, 2000);
                    });
                }
            }
        } catch (error) {
            console.error('Ses test hatası:', error);
            this.showNotification('Ses test edilemedi', 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Mevcut notification sistemini kullan
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            // Fallback: alert
            alert(message);
        }
    }
}

// Global instance
let voiceSelector;

// DOM hazır olduğunda başlat
document.addEventListener('DOMContentLoaded', () => {
    voiceSelector = new VoiceSelector();
});
