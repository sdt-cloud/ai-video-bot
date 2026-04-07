from flask import Blueprint, request, jsonify, render_template_string
from social_media_manager import SocialMediaManager
import json
import os

social_bp = Blueprint('social', __name__, url_prefix='/social')
manager = SocialMediaManager()

@social_bp.route('/')
def social_dashboard():
    """Sosyal medya yönetim paneli"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sosyal Medya Yönetimi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2><i class="fas fa-share-alt"></i> Sosyal Medya Yönetimi</h2>
        
        <!-- API Yapılandırma -->
        <div class="card mb-4">
            <div class="card-header">
                <h5><i class="fas fa-cog"></i> API Yapılandırma</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <h6>Ayrshare</h6>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="ayrshare_enabled">
                            <label class="form-check-label" for="ayrshare_enabled">Aktif</label>
                        </div>
                        <input type="password" class="form-control" id="ayrshare_key" placeholder="API Anahtarı">
                        <button class="btn btn-sm btn-primary mt-2" onclick="saveConfig('ayrshare')">Kaydet</button>
                    </div>
                    <div class="col-md-4">
                        <h6>Outstand</h6>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="outstand_enabled">
                            <label class="form-check-label" for="outstand_enabled">Aktif</label>
                        </div>
                        <input type="password" class="form-control" id="outstand_key" placeholder="API Anahtarı">
                        <button class="btn btn-sm btn-primary mt-2" onclick="saveConfig('outstand')">Kaydet</button>
                    </div>
                    <div class="col-md-4">
                        <h6>PostForMe</h6>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="postforme_enabled">
                            <label class="form-check-label" for="postforme_enabled">Aktif</label>
                        </div>
                        <input type="password" class="form-control" id="postforme_key" placeholder="API Anahtarı">
                        <button class="btn btn-sm btn-primary mt-2" onclick="saveConfig('postforme')">Kaydet</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Video Gönderme -->
        <div class="card mb-4">
            <div class="card-header">
                <h5><i class="fas fa-video"></i> Videoyu Sosyal Medyada Paylaş</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Video Seç</label>
                        <select class="form-select" id="video_select">
                            <option value="">Video seçin...</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Provider</label>
                        <select class="form-select" id="provider_select">
                            <option value="ayrshare">Ayrshare</option>
                            <option value="outstand">Outstand</option>
                            <option value="postforme">PostForMe</option>
                        </select>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Platformlar</label>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="platform_facebook" value="facebook">
                            <label class="form-check-label" for="platform_facebook">Facebook</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="platform_x" value="x">
                            <label class="form-check-label" for="platform_x">X (Twitter)</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="platform_instagram" value="instagram">
                            <label class="form-check-label" for="platform_instagram">Instagram</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="platform_tiktok" value="tiktok">
                            <label class="form-check-label" for="platform_tiktok">TikTok</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="platform_youtube" value="youtube">
                            <label class="form-check-label" for="platform_youtube">YouTube</label>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Gönderi Metni</label>
                        <textarea class="form-control" id="post_content" rows="3" placeholder="Gönderi metnini girin..."></textarea>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Zamanlama (Opsiyonel)</label>
                        <input type="datetime-local" class="form-control" id="schedule_time">
                    </div>
                    <div class="col-md-6 d-flex align-items-end">
                        <button class="btn btn-success" onclick="postVideo()">
                            <i class="fas fa-paper-plane"></i> Gönder
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Gönderi Geçmişi -->
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-history"></i> Gönderi Geçmişi</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Tarih</th>
                                <th>Video</th>
                                <th>Platformlar</th>
                                <th>Provider</th>
                                <th>Durum</th>
                                <th>İşlemler</th>
                            </tr>
                        </thead>
                        <tbody id="posts_history">
                            <!-- Dinamik olarak doldurulacak -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Sayfa yüklendiğinde
        document.addEventListener('DOMContentLoaded', function() {
            loadConfig();
            loadVideos();
            loadPostHistory();
        });

        // API yapılandırmasını yükle
        async function loadConfig() {
            try {
                const response = await fetch('/social/api/config');
                const config = await response.json();
                
                document.getElementById('ayrshare_enabled').checked = config.ayrshare.enabled;
                document.getElementById('ayrshare_key').value = config.ayrshare.api_key;
                document.getElementById('outstand_enabled').checked = config.outstand.enabled;
                document.getElementById('outstand_key').value = config.outstand.api_key;
                document.getElementById('postforme_enabled').checked = config.postforme.enabled;
                document.getElementById('postforme_key').value = config.postforme.api_key;
            } catch (error) {
                console.error('Config yüklenemedi:', error);
            }
        }

        // API yapılandırmasını kaydet
        async function saveConfig(provider) {
            const enabled = document.getElementById(provider + '_enabled').checked;
            const apiKey = document.getElementById(provider + '_key').value;
            
            try {
                const response = await fetch('/social/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({provider, api_key: apiKey, enabled})
                });
                
                if (response.ok) {
                    alert('Yapılandırma kaydedildi!');
                } else {
                    alert('Hata: ' + (await response.text()));
                }
            } catch (error) {
                alert('Hata: ' + error.message);
            }
        }

        // Videoları yükle
        async function loadVideos() {
            try {
                const response = await fetch('/api/videos/completed');
                const videos = await response.json();
                
                const select = document.getElementById('video_select');
                select.innerHTML = '<option value="">Video seçin...</option>';
                
                videos.forEach(video => {
                    const option = document.createElement('option');
                    option.value = video.id;
                    option.textContent = `${video.topic} (${video.created_at})`;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Videolar yüklenemedi:', error);
            }
        }

        // Videoyu gönder
        async function postVideo() {
            const videoId = document.getElementById('video_select').value;
            const provider = document.getElementById('provider_select').value;
            const content = document.getElementById('post_content').value;
            const scheduleTime = document.getElementById('schedule_time').value;
            
            const platforms = [];
            if (document.getElementById('platform_facebook').checked) platforms.push('facebook');
            if (document.getElementById('platform_x').checked) platforms.push('x');
            if (document.getElementById('platform_instagram').checked) platforms.push('instagram');
            if (document.getElementById('platform_tiktok').checked) platforms.push('tiktok');
            if (document.getElementById('platform_youtube').checked) platforms.push('youtube');
            
            if (!videoId) {
                alert('Lütfen video seçin!');
                return;
            }
            
            if (platforms.length === 0) {
                alert('Lütfen en az bir platform seçin!');
                return;
            }
            
            try {
                const response = await fetch('/social/api/post', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        video_id: parseInt(videoId),
                        platforms,
                        content,
                        schedule_time: scheduleTime || null,
                        provider
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    alert('Gönderi başarıyla oluşturuldu!');
                    loadPostHistory();
                } else {
                    alert('Hata: ' + (result.error || 'Bilinmeyen hata'));
                }
            } catch (error) {
                alert('Hata: ' + error.message);
            }
        }

        // Gönderi geçmişini yükle
        async function loadPostHistory() {
            try {
                const response = await fetch('/social/api/history');
                const posts = await response.json();
                
                const tbody = document.getElementById('posts_history');
                tbody.innerHTML = '';
                
                posts.forEach(post => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${post.created_at}</td>
                        <td>${post.topic}</td>
                        <td>${post.platforms.join(', ')}</td>
                        <td>${post.provider}</td>
                        <td><span class="badge bg-success">${post.status}</span></td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="viewPostResult('${post.id}')">
                                <i class="fas fa-eye"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Geçmiş yüklenemedi:', error);
            }
        }

        // Gönderi sonucunu görüntüle
        async function viewPostResult(postId) {
            try {
                const response = await fetch(`/social/api/post/${postId}`);
                const post = await response.json();
                
                alert('Gönderi Sonucu:\n\n' + JSON.stringify(post.result, null, 2));
            } catch (error) {
                alert('Hata: ' + error.message);
            }
        }
    </script>
</body>
</html>
    ''')

@social_bp.route('/api/config', methods=['GET'])
def get_config():
    """Mevcut API yapılandırmasını döndürür"""
    return jsonify(manager.api_configs)

@social_bp.route('/api/config', methods=['POST'])
def update_config():
    """API yapılandırmasını günceller"""
    data = request.json
    provider = data.get('provider')
    api_key = data.get('api_key')
    enabled = data.get('enabled', True)
    
    if manager.configure_api(provider, api_key, enabled):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Geçersiz provider"}), 400

@social_bp.route('/api/post', methods=['POST'])
def create_post():
    """Videoyu sosyal medyada gönderir"""
    data = request.json
    video_id = data.get('video_id')
    platforms = data.get('platforms', [])
    content = data.get('content')
    schedule_time = data.get('schedule_time')
    provider = data.get('provider', 'ayrshare')
    
    if not video_id or not platforms:
        return jsonify({"error": "Video ID ve platformlar gereklidir"}), 400
    
    result = manager.post_video_to_social_media(
        video_id=video_id,
        platforms=platforms,
        content=content,
        schedule_time=schedule_time,
        provider=provider
    )
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result)

@social_bp.route('/api/history')
def get_history():
    """Gönderi geçmişini döndürür"""
    limit = request.args.get('limit', 50, type=int)
    posts = manager.get_post_history(limit)
    return jsonify(posts)

@social_bp.route('/api/post/<int:post_id>')
def get_post(post_id):
    """Belirli bir gönderinin detaylarını döndürür"""
    with manager.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sp.*, v.topic, v.video_path 
            FROM social_posts sp
            JOIN videos v ON sp.video_id = v.id
            WHERE sp.id = ?
        """, (post_id,))
        
        post = cursor.fetchone()
        if not post:
            return jsonify({"error": "Gönderi bulunamadı"}), 404
        
        result = dict(post)
        result["platforms"] = json.loads(result["platforms"])
        result["result"] = json.loads(result["result"])
        
        return jsonify(result)

@social_bp.route('/api/platforms')
def get_platforms():
    """Desteklenen platformları döndürür"""
    return jsonify(manager.get_platform_list())
