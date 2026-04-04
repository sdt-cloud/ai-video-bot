document.addEventListener('DOMContentLoaded', () => {

    // --- Sidebar Menü Yönlendirmesi (Navigasyon) ---
    const navLinks = document.querySelectorAll('.nav-links li');
    const viewSections = document.querySelectorAll('.view-section');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.forEach(item => item.classList.remove('active'));
            link.classList.add('active');

            const targetId = link.getAttribute('data-target');
            viewSections.forEach(section => {
                if (section.id === targetId) {
                    section.classList.add('active');
                } else {
                    section.classList.remove('active');
                }
            });
            
            // Verileri tazele
            if (targetId === 'videos-view' || targetId === 'scripts-view' || targetId === 'media-view') {
                fetchVideos();
            }
        });
    });

    // --- Yeni Üretim (Generator) Sekmeleri ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const singleForm = document.getElementById('single-form');
    const bulkForm = document.getElementById('bulk-form');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tab = btn.getAttribute('data-tab');
            if (tab === 'single') {
                singleForm.classList.remove('d-none');
                bulkForm.classList.add('d-none');
            } else {
                bulkForm.classList.remove('d-none');
                singleForm.classList.add('d-none');
            }
        });
    });

    // --- API Entegrasyonu ---
    
    // Tekli Ekleme API Çağrısı
    const singleBtn = singleForm.querySelector('.primary-btn');
    singleBtn.addEventListener('click', async () => {
        const topicInput = singleForm.querySelector('input[type="text"]');
        const topic = topicInput.value;
        if(!topic) return alert("Lütfen bir konu giriniz!");

        const originalText = singleBtn.innerHTML;
        singleBtn.innerHTML = '<i data-feather="loader" class="spin"></i> Kuyruğa Ekleniyor...';
        feather.replace();
        
        try {
            const response = await fetch('/api/videos/single', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic: topic,
                    category: singleForm.querySelectorAll('input')[1].value || "Genel",
                    tone: singleForm.querySelectorAll('select')[0].value,
                    duration: parseInt(singleForm.querySelectorAll('select')[1].value),
                    language: singleForm.querySelectorAll('select')[2].value,
                    script_ai: singleForm.querySelectorAll('select')[3].value,
                    voice_ai: singleForm.querySelectorAll('select')[4].value,
                    image_ai: singleForm.querySelectorAll('select')[5].value,
                })
            });
            if(response.ok) {
                topicInput.value = '';
                alert("Konu başarıyla kuyruğa eklendi!");
                fetchStats();
            }
        } catch (e) {
            alert("Hata oluştu: " + e);
        } finally {
            singleBtn.innerHTML = originalText;
            feather.replace();
        }
    });

    // İstatistikleri çekme periyodik olarak
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            const data = await res.json();
            
            const statsPanel = document.querySelector('.stats-panel');
            if(!statsPanel) return;
            
            const boxes = statsPanel.querySelectorAll('strong');
            if(boxes.length >= 5) {
                boxes[0].innerText = data.pending;
                boxes[1].innerText = data.processing;
                boxes[2].innerText = data.completed;
                boxes[3].innerText = data.failed;
                boxes[4].innerText = data.total;
            }
            
            const progressBar = statsPanel.querySelector('.progress-bar');
            const percentLabel = statsPanel.querySelector('.progress-labels span:last-child');
            if(progressBar) {
                progressBar.style.width = data.success_rate + '%';
                percentLabel.innerText = '%' + data.success_rate;
            }
            
        } catch (e) {}
    }

    async function fetchVideos() {
        try {
            const res = await fetch('/api/videos');
            const data = await res.json();
            
            // Senaryolar tablosunu doldur
            const tbody = document.querySelector('#scripts-view tbody');
            if(tbody) {
                tbody.innerHTML = '';
                data.forEach(task => {
                    let badgeClass = "warning";
                    if(task.status === "completed") badgeClass = "success";
                    if(task.status === "failed") badgeClass = "danger";
                    
                    let statusTr = "Bekliyor";
                    if(task.status === "scripting") statusTr = "Senaryo Yazılıyor";
                    if(task.status === "media") statusTr = "Medya İndiriliyor";
                    if(task.status === "rendering") statusTr = "Kurgulanıyor";
                    if(task.status === "completed") statusTr = "Tamamlandı";
                    if(task.status === "failed") statusTr = "Hata Verildi";

                    tbody.innerHTML += `
                        <tr>
                            <td>${task.topic}</td>
                            <td><span class="badge ${badgeClass}">${statusTr}</span></td>
                            <td>${task.language.toUpperCase()}</td>
                            <td><button class="text-btn">ID: ${task.id}</button></td>
                        </tr>
                    `;
                });
            }

            // Oynatıcı Galerisini Doldur
            const gallery = document.querySelector('.video-gallery');
            if(gallery) {
                const completed = data.filter(t => t.status === 'completed');
                gallery.innerHTML = '';
                if(completed.length === 0) gallery.innerHTML = '<p>Henüz tamamlanmış video yok.</p>';
                
                completed.forEach(task => {
                    gallery.innerHTML += `
                        <div class="video-item">
                            <video src="/static/videos/${task.video_path}" controls style="width:100%; height:300px; background:#000;"></video>
                            <div class="video-info">
                                <h4>${task.topic}</h4>
                                <p>${task.duration} saniye • ${task.language.toUpperCase()}</p>
                                <div class="video-actions">
                                    <a href="/static/videos/${task.video_path}" download class="icon-btn" title="İndir"><i data-feather="download"></i></a>
                                </div>
                            </div>
                        </div>
                    `;
                });
                feather.replace();
            }

        } catch (e) {}
    }

    // İlk yükleme ve periyodik güncellemeler
    fetchStats();
    fetchVideos();
    setInterval(fetchStats, 5000); // 5 saniyede bir paneli güncelle
    setInterval(fetchVideos, 10000); // 10 sn'de bir detayları güncelle
});
