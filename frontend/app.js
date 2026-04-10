const translations = {
    "tr": {
        "nav_dashboard": "Kontrol Paneli",
        "nav_projects": "Projeler",
        "nav_templates": "Şablonlar (Toplu)",
        "nav_assets": "Video Galerisi",
        "nav_settings": "Ayarlar",
        "nav_help": "Yardım",
        "stat_total": "TOPLAM VİDEO",
        "stat_progress": "HAZIRLANAN",
        "stat_completed": "TAMAMLANAN",
        "dash_create_title": "Yeni Video Üret",
        "dash_new_video": "Yeni Video",
        "dash_video_topic": "Video Konusu / Senaryo İstemi",
        "dash_gen_btn": "VİDEO ÜRET",
        "dash_adv_options": "Gelişmiş Seçenekler",
        "opt_category": "Kategori",
        "opt_tone": "Ton",
        "opt_duration": "Süre",
        "opt_language": "Dil",
        "opt_script_ai": "Senaryo YZ",
        "opt_voice_ai": "Ses YZ",
        "opt_image_ai": "Görsel YZ",
        "opt_subtitle": "Altyazı Stili",
        "opt_video_mode": "Video Animasyon",
        "tone_energetic": "Enerjik ve Hızlı",
        "tone_mysterious": "Gizemli ve Derin",
        "tone_scientific": "Bilimsel ve Ciddi",
        "tone_funny": "Komik ve Eğlenceli",
        "queue_title": "Üretim Kuyruğu",
        "queue_empty": "Henüz kuyrukta video yok.",
        "queue_empty_hint": "Yukarıdan ilk videonuzu oluşturun!",
        "proj_title": "Projeler",
        "proj_subtitle": "Tüm video projeleriniz konusuna göre listelenir.",
        "table_topic": "Konu",
        "table_status": "Durum",
        "table_progress": "İlerleme",
        "table_lang": "Dil",
        "table_created": "Oluşturulma",
        "bulk_title": "Toplu Üretim",
        "bulk_subtitle": "Aynı anda birden fazla konuyu üretim kuyruğuna ekleyin.",
        "bulk_label": "Konu Listesi (Her satıra bir konu)",
        "bulk_btn": "TÜMÜNÜ KUYRUĞA EKLE",
        "delete_selected": "Seçilenleri Sil",
        "confirm_delete": "Seçilen projeleri silmek istediğinizden emin misiniz?",
        "delete_success": "Projeler başarıyla silindi.",
        "delete_error": "Silinirken bir hata oluştu.",
        "assets_title": "Tamamlanan Videolar",
        "assets_subtitle": "Biten videoları izleyin, indirin veya paylaşın.",
        "assets_empty": "Henüz tamamlanan video yok.",
        "set_subtitle": "YZ Modellerini ve tercihlerinizi yapılandırın.",
        "set_api": "API Anahtarları",
        "set_hint": ".env dosyasında yapılandırıldı.",
        "modal_download": "İndir",
        
        "placeholder_dash_input": "Video konseptinizi buraya açıklayın...",
        "placeholder_opt_cat": "Örn: Finans, Tarih, Teknoloji...",
        "placeholder_bulk": "Büyük İskender'in kayıp mezarı...\nGüneş sisteminin sonu nasıl olacak?\nYapay zeka meslekleri nasıl değiştirecek...",
        
        "status_pending": "Bekliyor",
        "status_scripting": "Senaryo Yazılıyor...",
        "status_media": "Medya İndiriliyor...",
        "status_rendering": "Video Kurgulanıyor...",
        "status_completed": "Tamamlandı",
        "status_failed": "Hata",
        "time_just_now": "Şimdi"
    },
    "en": {
        "nav_dashboard": "Dashboard",
        "nav_projects": "Projects",
        "nav_templates": "Templates (Bulk)",
        "nav_assets": "Video Gallery",
        "nav_settings": "Settings",
        "nav_help": "Help",
        "stat_total": "TOTAL VIDEOS",
        "stat_progress": "IN PROGRESS",
        "stat_completed": "COMPLETED",
        "dash_create_title": "Create New Video",
        "dash_new_video": "New Video",
        "dash_video_topic": "Video Topic / Prompt",
        "dash_gen_btn": "GENERATE VIDEO",
        "dash_adv_options": "Advanced Options",
        "opt_category": "Category",
        "opt_tone": "Tone",
        "opt_duration": "Duration",
        "opt_language": "Language",
        "opt_script_ai": "Script AI",
        "opt_voice_ai": "Voice AI",
        "opt_image_ai": "Image AI",
        "opt_subtitle": "Subtitle Style",
        "opt_video_mode": "Video Animation",
        "tone_energetic": "Energetic & Fast",
        "tone_mysterious": "Mysterious & Deep",
        "tone_scientific": "Scientific & Serious",
        "tone_funny": "Funny & Entertaining",
        "queue_title": "Production Queue",
        "queue_empty": "No videos in queue yet.",
        "queue_empty_hint": "Create your first video above!",
        "proj_title": "Projects",
        "proj_subtitle": "All your video projects organized by topic.",
        "table_topic": "Topic",
        "table_status": "Status",
        "table_progress": "Progress",
        "table_lang": "Language",
        "table_created": "Created",
        "bulk_title": "Bulk Import",
        "bulk_subtitle": "Add multiple topics to the production queue at once.",
        "bulk_label": "Topic List (one topic per line)",
        "bulk_btn": "ADD ALL TO QUEUE",
        "delete_selected": "Delete Selected",
        "confirm_delete": "Are you sure you want to delete the selected projects?",
        "delete_success": "Projects successfully deleted.",
        "delete_error": "Error during deletion.",
        "assets_title": "Completed Videos",
        "assets_subtitle": "Watch, download and share your finished videos.",
        "assets_empty": "No completed videos yet.",
        "set_subtitle": "Configure your AI models and preferences.",
        "set_api": "API Keys",
        "set_hint": "Configured in .env file",
        "modal_download": "Download",
        
        "placeholder_dash_input": "Describe your video concept here...",
        "placeholder_opt_cat": "e.g. Finance, History, Technology...",
        "placeholder_bulk": "The lost tomb of Alexander the Great...\nHow will the solar system end?\nHow AI is changing jobs...",
        
        "status_pending": "Pending",
        "status_scripting": "Drafting Script...",
        "status_media": "Downloading Media...",
        "status_rendering": "Rendering Video...",
        "status_completed": "Completed",
        "status_failed": "Failed",
        "time_just_now": "Just now"
    }
};

let currentLang = 'tr';

document.addEventListener('DOMContentLoaded', () => {

    // --- Language Switcher ---
    const langBtns = document.querySelectorAll('.lang-btn');
    
    function applyTranslations() {
        const langData = translations[currentLang];
        
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if(langData[key]) el.textContent = langData[key];
        });
        
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const translationKey = "placeholder_" + key.replace("dash_input_placeholder", "dash_input").replace("opt_cat_placeholder", "opt_cat").replace("bulk_placeholder", "bulk");
            if(langData[translationKey]) el.setAttribute('placeholder', langData[translationKey]);
        });
        
        document.documentElement.lang = currentLang;
    }
    
    langBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            currentLang = btn.getAttribute('data-lang');
            applyTranslations();
            fetchVideos(); // re-render dynamically generated texts
        });
    });

    applyTranslations();

    // --- Theme Switcher ---
    const themeBtn = document.getElementById('theme-toggle');
    
    // Check local storage for theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        if(themeBtn) themeBtn.querySelector('span').textContent = 'dark_mode';
    }
    
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            const isLight = document.body.classList.contains('light-theme');
            
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
            themeBtn.querySelector('span').textContent = isLight ? 'dark_mode' : 'light_mode';
        });
    }

    // --- Navigation ---
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const targetId = item.getAttribute('data-target');
            if(!targetId) return;

            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            viewSections.forEach(section => {
                if (section.id === targetId) section.classList.add('active');
                else section.classList.remove('active');
            });

            if (targetId === 'projects-view' || targetId === 'assets-view' || targetId === 'dashboard-view') {
                fetchVideos();
            }
        });
    });

    // --- Advanced Options Toggle ---
    const advancedToggle = document.getElementById('advanced-toggle');
    const advancedOptions = document.getElementById('advanced-options');
    
    if (advancedToggle && advancedOptions) {
        advancedToggle.addEventListener('click', () => {
            advancedOptions.classList.toggle('hidden');
            advancedToggle.classList.toggle('open');
        });
    }

    // --- Toast Notifications ---
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    
    function showToast(message, type = 'success') {
        if(!toast) return;
        toastMessage.textContent = message;
        toast.className = 'toast'; 
        toast.classList.add(type); 
        void toast.offsetWidth;
        toast.classList.add('show');
        toast.classList.remove('hidden');
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.classList.add('hidden'), 400);
        }, 3000);
    }

    // --- API Calls ---

    // 1. Single Generation
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const topicInput = document.getElementById('topic-input');
            const customScriptInput = document.getElementById('custom-script-input');
            const topic = topicInput.value.trim();
            const customScript = customScriptInput ? customScriptInput.value.trim() : "";
            
            if(!topic) {
                alert(currentLang === 'tr' ? "Lütfen bir konu / prompt giriniz!" : "Please enter a topic / prompt!");
                return;
            }

            const originalHtml = generateBtn.innerHTML;
            generateBtn.innerHTML = '<span class="material-symbols-rounded" style="animation: spin 1s linear infinite;">rotate_right</span> Processing...';
            generateBtn.disabled = true;

            try {
                const payload = {
                    topic: topic,
                    category: document.getElementById('opt-category').value.trim() || "Genel",
                    tone: document.getElementById('opt-tone').value,
                    duration: parseInt(document.getElementById('opt-duration').value),
                    language: document.getElementById('opt-language').value,
                    script_ai: document.getElementById('opt-script-ai').value,
                    custom_script: customScript || null,
                    voice_ai: document.getElementById('opt-voice-ai').value,
                    voice_type: document.getElementById('voice-type').value, // Ses tipi eklendi
                    image_ai: document.getElementById('opt-image-ai').value,
                    subtitle_style: document.getElementById('opt-subtitle-style').value,
                    video_mode: document.getElementById('opt-video-mode').value
                };

                const res = await fetch('/api/videos/single', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                if(res.ok) {
                    topicInput.value = '';
                    if (customScriptInput) customScriptInput.value = '';
                    showToast(currentLang === 'tr' ? "Video başarıyla kuyruğa eklendi!" : "Video successfully added to queue!");
                    fetchStats();
                    fetchVideos();
                } else {
                    showToast(currentLang === 'tr' ? "Kuyruğa eklenirken hata oluştu." : "Error adding to queue.", "error");
                }
            } catch (err) {
                console.error(err);
                showToast(currentLang === 'tr' ? "Sunucu ile bağlantı hatası." : "Server connection error.", "error");
            } finally {
                generateBtn.innerHTML = originalHtml;
                generateBtn.disabled = false;
            }
        });
    }

    // 2. Bulk Generation
    const bulkBtn = document.getElementById('bulk-btn');
    if (bulkBtn) {
        bulkBtn.addEventListener('click', async () => {
            const bulkTextarea = document.getElementById('bulk-textarea');
            const lines = bulkTextarea.value.split('\n').filter(line => line.trim().length > 0);

            if(lines.length === 0) {
                alert(currentLang === 'tr' ? "Lütfen en az bir konu giriniz!" : "Please enter at least one topic!");
                return;
            }

            const originalHtml = bulkBtn.innerHTML;
            bulkBtn.innerHTML = '<span class="material-symbols-rounded" style="animation: spin 1s linear infinite;">rotate_right</span> Processing...';
            bulkBtn.disabled = true;

            try {
                const payload = {
                    topics: lines,
                    duration: parseInt(document.getElementById('bulk-duration').value),
                    language: document.getElementById('bulk-language').value,
                    script_ai: document.getElementById('bulk-script-ai').value,
                    voice_ai: document.getElementById('bulk-voice-ai').value,
                    voice_type: document.getElementById('bulk-voice-type').value,
                    image_ai: document.getElementById('bulk-image-ai').value,
                    subtitle_style: document.getElementById('bulk-subtitle-style').value,
                    video_mode: document.getElementById('bulk-video-mode').value
                };

                const res = await fetch('/api/videos/bulk', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                if(res.ok) {
                    bulkTextarea.value = '';
                    showToast(currentLang === 'tr' ? `${lines.length} konu kuyruğa eklendi!` : `${lines.length} topics added to queue!`);
                    fetchStats();
                    fetchVideos();
                }
            } catch (err) {
                console.error(err);
                showToast(currentLang === 'tr' ? "Toplu işlem hatası." : "Bulk import error.", "error");
            } finally {
                bulkBtn.innerHTML = originalHtml;
                bulkBtn.disabled = false;
            }
        });
    }

    // 3. Stats Fetch
    function fetchStats() {
        fetch('/api/stats').then(res => res.json()).then(data => {
            const totalEl = document.getElementById('stat-total');
            const progressEl = document.getElementById('stat-progress');
            const completedEl = document.getElementById('stat-completed');
            
            if(totalEl) totalEl.textContent = data.total || 0;
            if(progressEl) progressEl.textContent = (data.pending || 0) + (data.processing || 0);
            if(completedEl) completedEl.textContent = data.completed || 0;
        }).catch(e => console.error(e));
    }

    // 4. Videos Fetch
    function fetchVideos() {
        const formatDuration = (seconds) => {
            const totalSeconds = Number(seconds) || 0;
            const minutes = Math.floor(totalSeconds / 60);
            const remaining = totalSeconds % 60;

            if (minutes === 0) {
                return `${totalSeconds}s`;
            }
            if (remaining === 0) {
                return `${minutes}m`;
            }
            return `${minutes}m ${remaining}s`;
        };

        const fallbackInfo = (task) => {
            const msg = (task.error_message || "").trim();
            return msg.startsWith("Bilgi:") ? msg : "";
        };

        const langData = translations[currentLang];
        fetch('/api/videos').then(res => res.json()).then(data => {
            // Queue Grid
            const queueGrid = document.getElementById('queue-grid');
            if (queueGrid) {
                const activeTasks = data.filter(t => t.status !== 'completed' && t.status !== 'failed');
                
                if (activeTasks.length === 0) {
                    queueGrid.innerHTML = `
                        <div class="empty-state">
                            <span class="material-symbols-rounded">movie_creation</span>
                            <p>${langData.queue_empty}</p>
                            <p class="hint">${langData.queue_empty_hint}</p>
                        </div>
                    `;
                } else {
                    queueGrid.innerHTML = '';
                    activeTasks.forEach(task => {
                        let statusText = langData.status_pending;
                        let isProcessing = false;
                        const infoMessage = fallbackInfo(task);
                        
                        if (task.status === "scripting") { statusText = langData.status_scripting; isProcessing = true; }
                        else if (task.status === "media") { statusText = langData.status_media; isProcessing = true; }
                        else if (task.status === "rendering") { statusText = langData.status_rendering; isProcessing = true; }
                        
                        queueGrid.innerHTML += `
                            <div class="queue-card ${isProcessing ? 'processing' : ''}">
                                <div class="queue-status-bar">
                                    <div class="queue-progress" style="width: ${task.progress || 0}%"></div>
                                </div>
                                <div class="queue-card-top">
                                    <div class="queue-topic">${task.topic}</div>
                                    <span class="material-symbols-rounded queue-icon">motion_photos_on</span>
                                </div>
                                <div class="queue-card-bottom">
                                    <span>${statusText}</span>
                                    <span>${task.progress || 0}%</span>
                                </div>
                                ${infoMessage ? `<div style="margin-top:8px;padding:6px 8px;border-radius:8px;background:rgba(99,102,241,0.15);color:#c7d2fe;font-size:12px;line-height:1.35;">${infoMessage}</div>` : ''}
                            </div>
                        `;
                    });
                }
            }
            
            // Projects Table
            const tbody = document.getElementById('projects-tbody');
            if (tbody) {
                const selectedIds = Array.from(document.querySelectorAll('.project-cb:checked')).map(cb => cb.value);
                tbody.innerHTML = '';
                data.forEach((task, index) => {
                    let badgeClass = "warning";
                    let statusLabel = langData.status_pending;
                    const infoMessage = fallbackInfo(task);

                    if(task.status === "completed") { badgeClass = "completed"; statusLabel = langData.status_completed; }
                    else if(task.status === "failed") { badgeClass = "failed"; statusLabel = langData.status_failed; }
                    else if(task.status === "scripting") statusLabel = langData.status_scripting;
                    else if(task.status === "media") statusLabel = langData.status_media;
                    else if(task.status === "rendering") statusLabel = langData.status_rendering;

                    const dateStr = task.created_at ? task.created_at.split(' ')[0] : langData.time_just_now;
                    const isChecked = selectedIds.includes(task.id.toString()) ? 'checked' : '';
                    
                    tbody.innerHTML += `
                        <tr>
                            <td style="text-align:center;"><input type="checkbox" class="project-cb" value="${task.id}" ${isChecked} style="width:16px;height:16px;cursor:pointer;accent-color:var(--accent-color);"></td>
                            <td>${index + 1}</td>
                            <td>
                                <div>${task.topic}</div>
                                ${infoMessage ? `<div style="margin-top:6px;color:#c7d2fe;font-size:12px;line-height:1.3;">${infoMessage}</div>` : ''}
                            </td>
                            <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
                            <td>${task.progress || 0}%</td>
                            <td>${(task.language || 'TR').toUpperCase()}</td>
                            <td style="color:var(--text-secondary)">${dateStr}</td>
                        </tr>
                    `;
                });
            }

            // Video Gallery (Assets)
            const gallery = document.getElementById('video-gallery');
            if (gallery) {
                const completed = data.filter(t => t.status === 'completed');
                if (completed.length === 0) {
                    gallery.innerHTML = `
                        <div class="empty-state">
                            <span class="material-symbols-rounded">movie</span>
                            <p>${langData.assets_empty}</p>
                        </div>
                    `;
                } else {
                    gallery.innerHTML = '';
                    completed.forEach(task => {
                        const vidPath = `/static/videos/${task.video_path}`;
                        const cleanTopic = task.topic.replace(/'/g, "\\'");
                        const card = document.createElement('div');
                        card.className = 'video-card';
                        card.innerHTML = `
                            <div class="video-thumb" onclick="openModal('${vidPath}', '${cleanTopic}')">
                                <span class="material-symbols-rounded">play_circle</span>
                            </div>
                            <div class="video-details">
                                <h4 class="video-title" title="${task.topic}">${task.topic}</h4>
                                <div class="video-meta">
                                    <span>${formatDuration(task.duration)}</span>
                                    <span>${(task.language || 'TR').toUpperCase()}</span>
                                </div>
                                <div class="video-actions">
                                    <button class="action-btn btn-primary" onclick="openModal('${vidPath}', '${cleanTopic}')">
                                        <span class="material-symbols-rounded" style="font-size:18px;">play_arrow</span>
                                    </button>
                                    <a class="action-btn btn-secondary" href="${vidPath}" download>
                                        <span class="material-symbols-rounded" style="font-size:18px;">download</span> ${langData.modal_download}
                                    </a>
                                </div>
                            </div>
                        `;
                        gallery.appendChild(card);
                    });
                }
            }
        }).catch(e => console.error(e));
    }

    // Refresh queue button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.classList.add('spin');
            fetchStats();
            fetchVideos();
            setTimeout(() => refreshBtn.classList.remove('spin'), 500);
        });
    }

    // Modal logic
    window.openModal = function(src, title) {
        const modal = document.getElementById('video-modal');
        const video = document.getElementById('modal-video');
        const titleEl = document.getElementById('modal-title');
        const downloadEl = document.getElementById('modal-download');
        
        if (modal && video) {
            video.src = src;
            titleEl.textContent = title;
            downloadEl.href = src;
            
            modal.classList.remove('hidden');
            void modal.offsetWidth;
            modal.classList.add('active');
            
            video.play().catch(e => console.log("Autoplay prevented:", e));
        }
    }
    
    const modalClose = document.getElementById('modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            const modal = document.getElementById('video-modal');
            const video = document.getElementById('modal-video');
            
            modal.classList.remove('active');
            setTimeout(() => {
                modal.classList.add('hidden');
                if(video) {
                    video.pause();
                    video.src = '';
                }
            }, 300);
        });
    }

    // Bulk Delete Logic
    const selectAllCb = document.getElementById('select-all-projects');
    const pTbody = document.getElementById('projects-tbody');
    const deleteBtn = document.getElementById('delete-selected-btn');

    function updateDeleteBtnVisibility() {
        if(!deleteBtn) return;
        const anyChecked = document.querySelectorAll('.project-cb:checked').length > 0;
        if(anyChecked) {
            deleteBtn.style.display = 'flex';
        } else {
            deleteBtn.style.display = 'none';
            if(selectAllCb) selectAllCb.checked = false;
        }
    }

    if(selectAllCb && pTbody) {
        selectAllCb.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            document.querySelectorAll('.project-cb').forEach(cb => cb.checked = isChecked);
            updateDeleteBtnVisibility();
        });

        pTbody.addEventListener('change', (e) => {
            if(e.target.classList.contains('project-cb')) {
                updateDeleteBtnVisibility();
                const totalCb = document.querySelectorAll('.project-cb').length;
                const checkedCb = document.querySelectorAll('.project-cb:checked').length;
                selectAllCb.checked = (totalCb > 0 && totalCb === checkedCb);
            }
        });
    }

    if(deleteBtn) {
        deleteBtn.addEventListener('click', async () => {
            const checkedBoxes = document.querySelectorAll('.project-cb:checked');
            if(checkedBoxes.length === 0) return;
            
            const langData = translations[currentLang];
            if(!confirm(langData.confirm_delete)) return;

            const ids = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
            
            try {
                deleteBtn.innerHTML = '<span class="material-symbols-rounded spin">rotate_right</span>';
                deleteBtn.disabled = true;

                const res = await fetch('/api/videos', {
                    method: 'DELETE',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ task_ids: ids })
                });

                if(res.ok) {
                    showToast(langData.delete_success);
                    if(selectAllCb) selectAllCb.checked = false;
                    deleteBtn.style.display = 'none';
                    fetchStats();
                    fetchVideos();
                } else {
                    showToast(langData.delete_error, "error");
                }
            } catch(e) {
                console.error(e);
                showToast(langData.delete_error, "error");
            } finally {
                deleteBtn.innerHTML = `<span class="material-symbols-rounded">delete</span> <span data-i18n="delete_selected" style="font-weight:600;font-size:0.9rem;">${langData.delete_selected}</span>`;
                deleteBtn.disabled = false;
            }
        });
    }

    // 3. Nedir.me Integration
    const nedirFetchBtn = document.getElementById('nedir-fetch-btn');
    if (nedirFetchBtn) {
        nedirFetchBtn.addEventListener('click', async () => {
            const postType = document.getElementById('nedir-type-select').value;
            const resultsDiv = document.getElementById('nedir-results');
            const submitBtn = document.getElementById('nedir-submit-btn');
            const optionsDiv = document.getElementById('nedir-options');
            
            nedirFetchBtn.innerHTML = '<span class="material-symbols-rounded" style="animation: spin 1s linear infinite;">rotate_right</span> Fetching...';
            nedirFetchBtn.disabled = true;
            
            try {
                const res = await fetch(`/api/nedir/fetch?post_type=${postType}&limit=20`);
                const data = await res.json();
                
                if (data.status === 'success') {
                    const meta = data.meta || {};
                    const metaHtml = meta.total_posts ? `
                        <div style="margin-bottom:1rem; padding:0.6rem 1rem; background:rgba(99,102,241,0.1); border-radius:8px; font-size:0.82rem; color:var(--accent-color); display:flex; gap:1.5rem; flex-wrap:wrap;">
                            <span>📊 Toplam: <strong>${meta.total_posts}</strong> içerik</span>
                            <span>📄 Rastgele Sayfa: <strong>${meta.page} / ${meta.total_pages}</strong></span>
                            ${meta.skipped_already_done > 0 ? `<span>✅ Zaten Yapılmış: <strong>${meta.skipped_already_done}</strong> adet atlandı</span>` : ''}
                        </div>` : '';

                    if (data.data.length === 0) {
                        resultsDiv.innerHTML = metaHtml + `<p style="padding:1rem;color:var(--text-color);">Bu sayfadaki tüm içerikler zaten kuyruğa eklenmiş. Tekrar Fetch Data'ya bas — farklı bir rastgele sayfadan içerik gelecek!</p>`;
                        submitBtn.style.display = 'none';
                        optionsDiv.style.display = 'none';
                    } else {
                        let html = metaHtml;
                        data.data.forEach(item => {
                            // Basit bir checkbox ve açıklama kutusu
                            html += `
                            <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:15px; padding-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.05);">
                                <input type="checkbox" class="nedir-cb" value="${item.id}" style="margin-top:5px; accent-color:var(--accent-color);" checked>
                                <div>
                                    <h4 style="margin:0 0 5px 0; color:var(--text-color);">${item.title}</h4>
                                    <p style="margin:0; font-size:0.85rem; color:#888;" class="nedir-desc" data-title="${item.title}">${item.excerpt}</p>
                                </div>
                            </div>
                            `;
                        });
                        resultsDiv.innerHTML = html;
                        submitBtn.style.display = 'flex';
                        optionsDiv.style.display = 'flex';
                    }
                    resultsDiv.style.display = 'block';

                } else {
                    showToast(data.message, "error");
                }
            } catch (err) {
                console.error(err);
                showToast("API bağlantı hatası. .env dosyasını kontrol edin.", "error");
            } finally {
                nedirFetchBtn.innerHTML = '<span class="material-symbols-rounded">cloud_sync</span> <span data-i18n="nedir_fetch">Fetch Data</span>';
                nedirFetchBtn.disabled = false;
                applyTranslations();
            }
        });
    }

    const nedirSubmitBtn = document.getElementById('nedir-submit-btn');
    if (nedirSubmitBtn) {
        nedirSubmitBtn.addEventListener('click', async () => {
            const checkboxes = document.querySelectorAll('.nedir-cb:checked');
            if (checkboxes.length === 0) {
                alert("Lütfen en az bir içerik seçin!");
                return;
            }

            const lines = [];
            checkboxes.forEach(cb => {
                const descP = cb.nextElementSibling.querySelector('.nedir-desc');
                const title = descP.getAttribute('data-title');
                const excerpt = descP.textContent;
                lines.push(`Nedir.me Konusu: ${title} - Özeti: ${excerpt}`);
            });

            const originalHtml = nedirSubmitBtn.innerHTML;
            nedirSubmitBtn.innerHTML = '<span class="material-symbols-rounded" style="animation: spin 1s linear infinite;">rotate_right</span> Processing...';
            nedirSubmitBtn.disabled = true;

            try {
                const payload = {
                    topics: lines,
                    duration: parseInt(document.getElementById('nedir-duration').value),
                    language: 'tr', // Nedir.me Türkçe
                    script_ai: document.getElementById('nedir-script-ai').value,
                    voice_ai: document.getElementById('nedir-voice-ai').value,
                    image_ai: document.getElementById('nedir-image-ai').value,
                    subtitle_style: document.getElementById('nedir-subtitle-style').value,
                    video_mode: document.getElementById('nedir-video-mode').value
                };

                const res = await fetch('/api/videos/bulk', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                if(res.ok) {
                    showToast(`${lines.length} adet konu başarıyla kuyruğa eklendi!`);
                    document.getElementById('nedir-results').innerHTML = '';
                    document.getElementById('nedir-results').style.display = 'none';
                    document.getElementById('nedir-options').style.display = 'none';
                    nedirSubmitBtn.style.display = 'none';
                    fetchStats();
                    fetchVideos();
                    // Queue sayfasına git
                    document.querySelector('.nav-item[data-target="dashboard-view"]').click();
                } else {
                    showToast("Kuyruğa eklenirken hata oluştu.", "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Sunucu ile bağlantı hatası.", "error");
            } finally {
                nedirSubmitBtn.innerHTML = originalHtml;
                nedirSubmitBtn.disabled = false;
            }
        });
    }

    // Initial fetch & intervals
    fetchStats();
    fetchVideos();
    setInterval(fetchStats, 5000);
    setInterval(fetchVideos, 10000);
});
