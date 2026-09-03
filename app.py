from flask import Flask, request, jsonify, render_template_string, Response
import yt_dlp
import logging
import os
import json
from functools import lru_cache

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache Engine: ভিডিও লোড স্পিড 0 সেকেন্ড করার জন্য
@lru_cache(maxsize=500)
def get_cached_video_url(page_url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'noplaylist': True,
        'socket_timeout': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(page_url, download=False)
            if 'url' in info:
                return info['url'], info.get('title', 'Unknown Video')
            elif 'formats' in info and len(info['formats']) > 0:
                best_format = info['formats'][-1]
                return best_format['url'], info.get('title', 'Unknown Video')
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None, None
    return None, None

@app.route('/')
def index():
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="bn">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
            <meta name="theme-color" content="#0f172a">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
            <title>PlayX - Premium Player</title>
            
            <!-- PWA Manifest -->
            <link rel="manifest" href="/manifest.json">
            <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/5725/5725055.png">
            
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            
            <style>
                :root { --primary: #0ea5e9; }
                body { background-color: #0f172a; color: white; -webkit-tap-highlight-color: transparent; overscroll-behavior-y: contain; font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
                .glass { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
                .hide-controls { opacity: 0; pointer-events: none; transition: opacity 0.5s ease; }
                .show-controls { opacity: 1; pointer-events: auto; transition: opacity 0.3s ease; }
                input[type=range] { accent-color: var(--primary); }
                .loader { width: 48px; height: 48px; border: 3px solid rgba(255,255,255,0.1); border-radius: 50%; border-top-color: var(--primary); animation: spin 1s ease-in-out infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
                
                /* Animations */
                .slide-up { animation: slideUp 0.4s ease forwards; }
                @keyframes slideUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
            </style>
        </head>
        <body class="h-[100dvh] w-screen overflow-hidden flex flex-col selection:bg-sky-500/30">
            
            <!-- App Header -->
            <div id="app-header" class="px-6 py-4 flex justify-between items-center glass z-10">
                <div class="flex items-center gap-3">
                    <div class="bg-gradient-to-tr from-sky-400 to-blue-600 p-2 rounded-xl shadow-lg shadow-sky-500/20">
                        <i class="fa-solid fa-play text-white text-xl"></i>
                    </div>
                    <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">PlayX</h1>
                </div>
                <button onclick="installApp()" id="install-btn" class="hidden bg-white/10 hover:bg-white/20 px-4 py-2 rounded-full text-sm font-medium backdrop-blur-md transition">
                    <i class="fa-solid fa-download mr-1"></i> Install App
                </button>
            </div>

            <!-- Home Screen -->
            <div id="home-screen" class="flex-1 overflow-y-auto p-6 flex flex-col items-center w-full max-w-2xl mx-auto pb-20">
                
                <div class="w-full glass p-2 rounded-2xl flex items-center shadow-2xl mt-6 mb-8 group focus-within:ring-2 focus-within:ring-sky-500/50 transition-all">
                    <div class="pl-4 text-slate-400"><i class="fa-solid fa-link"></i></div>
                    <input type="url" id="video-url" placeholder="Enter video link here..." class="w-full bg-transparent border-none outline-none px-4 py-3 text-white placeholder-slate-500 text-lg">
                    <button onclick="processVideo()" class="bg-sky-500 hover:bg-sky-400 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-sky-500/30">
                        Play <i class="fa-solid fa-arrow-right ml-1"></i>
                    </button>
                </div>

                <!-- Features Grid -->
                <div class="grid grid-cols-3 gap-4 w-full mb-10">
                    <div class="glass p-4 rounded-2xl text-center"><i class="fa-solid fa-bolt text-yellow-400 text-2xl mb-2"></i><p class="text-xs text-slate-400">Zero Delay</p></div>
                    <div class="glass p-4 rounded-2xl text-center"><i class="fa-solid fa-shield-halved text-emerald-400 text-2xl mb-2"></i><p class="text-xs text-slate-400">Ad Free</p></div>
                    <div class="glass p-4 rounded-2xl text-center"><i class="fa-solid fa-cloud-arrow-down text-sky-400 text-2xl mb-2"></i><p class="text-xs text-slate-400">Download</p></div>
                </div>

                <!-- History -->
                <div class="w-full text-left">
                    <h3 class="text-slate-300 font-bold mb-4 flex items-center gap-2 text-lg">
                        <i class="fa-solid fa-history text-sky-400"></i> Recent Plays
                    </h3>
                    <div id="history-list" class="space-y-3"></div>
                </div>
            </div>

            <!-- Loading UI -->
            <div id="loading-screen" class="hidden fixed inset-0 bg-slate-900/95 z-50 flex flex-col items-center justify-center backdrop-blur-md">
                <div class="loader mb-6"></div>
                <h2 class="text-xl font-bold text-white mb-2">Extracting Video...</h2>
                <p class="text-sky-400 text-sm font-medium animate-pulse">Bypassing servers for high quality</p>
            </div>

            <!-- Full Screen Player -->
            <div id="player-screen" class="hidden fixed inset-0 bg-black z-50 flex items-center justify-center">
                <video id="main-video" class="w-full h-full object-contain" playsinline crossorigin="anonymous"></video>
                
                <!-- Controls Overlay -->
                <div id="controls-overlay" class="absolute inset-0 flex flex-col justify-between show-controls transition-all duration-300">
                    
                    <!-- Top Bar -->
                    <div class="glass p-4 pt-8 md:pt-4 flex justify-between items-center bg-gradient-to-b from-black/90 to-transparent">
                        <button onclick="closePlayer()" class="text-white hover:text-sky-400 text-2xl w-10 h-10 flex items-center justify-center rounded-full bg-black/20 backdrop-blur"><i class="fa-solid fa-chevron-down"></i></button>
                        <h2 id="video-title" class="text-white text-sm font-medium truncate px-4 flex-1 text-center shadow-black drop-shadow-md">Title</h2>
                        <div class="flex gap-3">
                            <button onclick="togglePiP()" class="text-white hover:text-sky-400 text-xl w-10 h-10 rounded-full bg-black/20"><i class="fa-solid fa-clone"></i></button>
                            <button onclick="toggleLock()" class="text-white hover:text-sky-400 text-xl w-10 h-10 rounded-full bg-black/20" id="lock-btn"><i class="fa-solid fa-unlock"></i></button>
                        </div>
                    </div>

                    <!-- Center Loading Buffer -->
                    <div id="buffer-loader" class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 hidden">
                        <div class="loader"></div>
                    </div>

                    <!-- Double Tap Zones -->
                    <div class="absolute inset-0 top-20 bottom-32 flex z-0" id="tap-zones">
                        <div class="w-1/3 h-full flex items-center justify-center" ondblclick="skip(-10)">
                            <div class="hidden bg-black/50 text-white p-3 rounded-full animate-ping" id="rewind-indicator"><i class="fa-solid fa-backward"></i></div>
                        </div>
                        <div class="w-1/3 h-full cursor-pointer" onclick="togglePlay()"></div>
                        <div class="w-1/3 h-full flex items-center justify-center" ondblclick="skip(10)">
                            <div class="hidden bg-black/50 text-white p-3 rounded-full animate-ping" id="forward-indicator"><i class="fa-solid fa-forward"></i></div>
                        </div>
                    </div>

                    <!-- Bottom Bar -->
                    <div class="glass p-5 flex flex-col gap-4 bg-gradient-to-t from-black via-black/80 to-transparent z-10 w-full" id="bottom-controls">
                        
                        <!-- Timeline -->
                        <div class="flex items-center gap-4 text-sm font-medium text-slate-200">
                            <span id="current-time">00:00</span>
                            <div class="relative flex-1 group h-2 cursor-pointer" id="progress-container" onclick="seek(event)">
                                <div class="absolute inset-0 bg-slate-600/50 rounded-full"></div>
                                <div class="absolute inset-y-0 left-0 bg-sky-500 rounded-full w-0 relative" id="progress-bar">
                                    <div class="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow scale-0 group-hover:scale-100 transition-transform"></div>
                                </div>
                            </div>
                            <span id="duration">00:00</span>
                        </div>

                        <!-- Controls -->
                        <div class="flex justify-between items-center">
                            <!-- Left Controls -->
                            <div class="flex items-center gap-6">
                                <button onclick="togglePlay()" id="play-btn" class="text-3xl text-white hover:text-sky-400 transition-transform active:scale-90"><i class="fa-solid fa-play"></i></button>
                                <button onclick="skip(-10)" class="text-xl text-slate-300 hover:text-white"><i class="fa-solid fa-rotate-left"></i></button>
                                <button onclick="skip(10)" class="text-xl text-slate-300 hover:text-white"><i class="fa-solid fa-rotate-right"></i></button>
                            </div>
                            
                            <!-- Right Controls -->
                            <div class="flex items-center gap-5">
                                <!-- Speed -->
                                <button onclick="changeSpeed()" id="speed-btn" class="text-sm font-bold bg-white/20 px-2 py-1 rounded text-white">1x</button>
                                
                                <!-- Audio / Brightness Dropups (Mobile friendly) -->
                                <div class="hidden md:flex items-center gap-4">
                                    <i class="fa-solid fa-sun text-slate-300"></i>
                                    <input type="range" id="brightness-bar" min="20" max="200" value="100" class="w-20">
                                </div>
                                <div class="hidden md:flex items-center gap-4">
                                    <i class="fa-solid fa-volume-high text-slate-300" id="vol-icon"></i>
                                    <input type="range" id="volume-bar" min="0" max="1" step="0.1" value="1" class="w-20">
                                </div>
                                
                                <button onclick="startDownload()" class="text-xl text-sky-400 hover:text-sky-300 ml-2"><i class="fa-solid fa-download"></i></button>
                                <button onclick="toggleFullScreen()" class="text-xl text-slate-300 hover:text-white ml-2"><i class="fa-solid fa-expand"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Service Worker Script for PWA -->
            <script>
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.register('/sw.js').then(() => {
                        console.log('Service Worker Registered');
                    });
                }
                
                // Add to Home Screen Logic
                let deferredPrompt;
                window.addEventListener('beforeinstallprompt', (e) => {
                    e.preventDefault();
                    deferredPrompt = e;
                    document.getElementById('install-btn').classList.remove('hidden');
                });
                
                function installApp() {
                    if (deferredPrompt) {
                        deferredPrompt.prompt();
                        deferredPrompt.userChoice.then((choiceResult) => {
                            if (choiceResult.outcome === 'accepted') {
                                document.getElementById('install-btn').classList.add('hidden');
                            }
                            deferredPrompt = null;
                        });
                    }
                }
            </script>

            <!-- Main App Script -->
            <script>
                // Core Elements
                const video = document.getElementById('main-video');
                const controlsOverlay = document.getElementById('controls-overlay');
                let hls = null;
                let controlsTimeout;
                let currentVideoUrl = '';
                let isLocked = false;
                const speeds = [1, 1.25, 1.5, 2, 0.5];
                let speedIndex = 0;

                async function processVideo(url = null) {
                    const finalUrl = url || document.getElementById('video-url').value;
                    if (!finalUrl) return alert("Please paste a valid video link.");

                    document.getElementById('loading-screen').classList.remove('hidden');

                    try {
                        const res = await fetch('/api/extract', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url: finalUrl })
                        });
                        const data = await res.json();

                        if (data.success) {
                            saveHistory(finalUrl, data.title);
                            openPlayer(data.direct_url, data.title);
                        } else {
                            alert("This video format or site is not supported/protected.");
                        }
                    } catch (err) {
                        alert("Network error.");
                    } finally {
                        document.getElementById('loading-screen').classList.add('hidden');
                    }
                }

                function openPlayer(streamUrl, title) {
                    document.getElementById('home-screen').classList.add('hidden');
                    document.getElementById('app-header').classList.add('hidden');
                    document.getElementById('player-screen').classList.remove('hidden');
                    document.getElementById('video-title').innerText = title;
                    currentVideoUrl = streamUrl;
                    
                    // Reset States
                    isLocked = false;
                    document.getElementById('lock-btn').innerHTML = '<i class="fa-solid fa-unlock"></i>';
                    document.getElementById('bottom-controls').style.display = 'flex';
                    document.getElementById('tap-zones').style.pointerEvents = 'auto';

                    if (Hls.isSupported() && streamUrl.includes('.m3u8')) {
                        if(hls) hls.destroy();
                        hls = new Hls();
                        hls.loadSource(streamUrl);
                        hls.attachMedia(video);
                        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
                    } else {
                        video.src = streamUrl;
                        video.play();
                    }
                    resetControlsTimer();
                }

                function closePlayer() {
                    video.pause();
                    video.src = '';
                    if(hls) hls.destroy();
                    document.getElementById('player-screen').classList.add('hidden');
                    document.getElementById('home-screen').classList.remove('hidden');
                    document.getElementById('app-header').classList.remove('hidden');
                    if(document.fullscreenElement) document.exitFullscreen();
                    loadHistory();
                }

                // Controls Logic
                function togglePlay() {
                    video.paused ? video.play() : video.pause();
                }
                
                video.addEventListener('play', () => document.getElementById('play-btn').innerHTML = '<i class="fa-solid fa-pause"></i>');
                video.addEventListener('pause', () => document.getElementById('play-btn').innerHTML = '<i class="fa-solid fa-play ml-1"></i>');

                // Advanced Features
                function toggleLock() {
                    isLocked = !isLocked;
                    const btn = document.getElementById('lock-btn');
                    const bottomControls = document.getElementById('bottom-controls');
                    const tapZones = document.getElementById('tap-zones');
                    
                    if(isLocked) {
                        btn.innerHTML = '<i class="fa-solid fa-lock text-red-500"></i>';
                        bottomControls.style.display = 'none';
                        tapZones.style.pointerEvents = 'none'; // Disable tap to pause/seek
                    } else {
                        btn.innerHTML = '<i class="fa-solid fa-unlock"></i>';
                        bottomControls.style.display = 'flex';
                        tapZones.style.pointerEvents = 'auto';
                    }
                }

                function togglePiP() {
                    if (document.pictureInPictureElement) {
                        document.exitPictureInPicture();
                    } else if (document.pictureInPictureEnabled) {
                        video.requestPictureInPicture();
                    } else {
                        alert("Picture in Picture is not supported in this browser.");
                    }
                }

                function changeSpeed() {
                    speedIndex = (speedIndex + 1) % speeds.length;
                    video.playbackRate = speeds[speedIndex];
                    document.getElementById('speed-btn').innerText = speeds[speedIndex] + 'x';
                }

                // Progress Bar
                function formatTime(sec) {
                    if(isNaN(sec)) return "00:00";
                    let m = Math.floor(sec / 60);
                    let s = Math.floor(sec % 60);
                    return `${m < 10 ? '0'+m : m}:${s < 10 ? '0'+s : s}`;
                }

                video.addEventListener('timeupdate', () => {
                    const percent = (video.currentTime / video.duration) * 100;
                    document.getElementById('progress-bar').style.width = percent + '%';
                    document.getElementById('current-time').innerText = formatTime(video.currentTime);
                });
                
                video.addEventListener('loadedmetadata', () => {
                    document.getElementById('duration').innerText = formatTime(video.duration);
                });

                function seek(e) {
                    const rect = document.getElementById('progress-container').getBoundingClientRect();
                    const pos = (e.clientX - rect.left) / rect.width;
                    video.currentTime = pos * video.duration;
                }

                function skip(amount) {
                    if(isLocked) return;
                    video.currentTime += amount;
                    // Visual feedback
                    const ind = amount > 0 ? document.getElementById('forward-indicator') : document.getElementById('rewind-indicator');
                    ind.classList.remove('hidden');
                    setTimeout(() => ind.classList.add('hidden'), 500);
                    resetControlsTimer();
                }

                // Fullscreen
                function toggleFullScreen() {
                    if (!document.fullscreenElement) {
                        document.getElementById('player-screen').requestFullscreen().catch(err => console.log(err));
                    } else {
                        document.exitFullscreen();
                    }
                }

                // Auto-Hide Controls
                function resetControlsTimer() {
                    if(isLocked) {
                        controlsOverlay.classList.remove('hide-controls');
                        clearTimeout(controlsTimeout);
                        controlsTimeout = setTimeout(() => controlsOverlay.classList.add('hide-controls'), 3000);
                        return;
                    }
                    controlsOverlay.classList.remove('hide-controls');
                    clearTimeout(controlsTimeout);
                    controlsTimeout = setTimeout(() => {
                        if (!video.paused) controlsOverlay.classList.add('hide-controls');
                    }, 4000);
                }
                
                document.getElementById('player-screen').addEventListener('mousemove', resetControlsTimer);
                document.getElementById('player-screen').addEventListener('touchstart', resetControlsTimer);
                document.getElementById('player-screen').addEventListener('click', resetControlsTimer);

                // Buffering
                video.addEventListener('waiting', () => document.getElementById('buffer-loader').classList.remove('hidden'));
                video.addEventListener('playing', () => document.getElementById('buffer-loader').classList.add('hidden'));

                // Downloader Engine
                function startDownload() {
                    if (currentVideoUrl.includes('.m3u8')) {
                        alert("⚠️ এটি HLS লাইভ/স্ট্রিমিং ভিডিও। এটি সরাসরি ডাউনলোড সাপোর্ট করে না, তবে আপনি প্লেয়ারে দেখতে পারবেন।");
                    } else {
                        // Create virtual download element
                        const a = document.createElement('a');
                        a.href = currentVideoUrl;
                        a.target = '_blank';
                        a.download = 'PlayX_Video.mp4'; // Suggest filename
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    }
                }

                // Brightness & Volume (Desktop)
                document.getElementById('brightness-bar')?.addEventListener('input', (e) => {
                    video.style.filter = `brightness(${e.target.value}%)`;
                });
                document.getElementById('volume-bar')?.addEventListener('input', (e) => {
                    video.volume = e.target.value;
                });

                // History
                function saveHistory(url, title) {
                    let history = JSON.parse(localStorage.getItem('playx_history')) || [];
                    history = history.filter(item => item.url !== url);
                    history.unshift({ url, title });
                    if(history.length > 15) history.pop();
                    localStorage.setItem('playx_history', JSON.stringify(history));
                }

                function loadHistory() {
                    const history = JSON.parse(localStorage.getItem('playx_history')) || [];
                    const list = document.getElementById('history-list');
                    if(history.length === 0){
                        list.innerHTML = '<div class="glass p-6 rounded-2xl text-center text-slate-500">কোনো হিস্ট্রি নেই</div>';
                        return;
                    }
                    list.innerHTML = history.map(item => `
                        <div onclick="processVideo('${item.url}')" class="glass p-4 rounded-xl flex justify-between items-center cursor-pointer hover:bg-slate-800 transition shadow-lg slide-up">
                            <div class="overflow-hidden pr-4 flex items-center gap-4">
                                <div class="bg-slate-700 w-10 h-10 rounded-lg flex items-center justify-center text-sky-400">
                                    <i class="fa-solid fa-play"></i>
                                </div>
                                <div>
                                    <h4 class="text-sm font-semibold text-white truncate max-w-[200px] md:max-w-md">${item.title}</h4>
                                    <p class="text-[10px] text-slate-400 truncate max-w-[200px] md:max-w-md mt-1">${item.url}</p>
                                </div>
                            </div>
                        </div>
                    `).join('');
                }

                window.onload = loadHistory;
            </script>
        </body>
        </html>
    """)

@app.route('/api/extract', methods=['POST'])
def extract_api():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({"success": False, "error": "No URL provided"}), 400
    
    # ⚡ ক্যাশ ফাংশন কল করা হলো (যাতে আগে দেখা ভিডিও ০ সেকেন্ডে লোড হয়)
    direct_url, title = get_cached_video_url(video_url)
    
    if direct_url:
        return jsonify({
            "success": True, 
            "direct_url": direct_url, 
            "title": title
        })
    return jsonify({"success": False, "error": "Failed to extract"}), 500

# ----------------------------------------------------
# PWA (Progressive Web App) Routes for "Add to Home Screen"
# ----------------------------------------------------
@app.route('/manifest.json')
def serve_manifest():
    manifest = {
        "name": "PlayX Premium Player",
        "short_name": "PlayX",
        "description": "Universal Ad-Free Fast Video Player",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/5725/5725055.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return Response(json.dumps(manifest), mimetype='application/json')

@app.route('/sw.js')
def serve_sw():
    sw_code = """
    self.addEventListener('install', (e) => {
        console.log('Service Worker: Installed');
    });
    self.addEventListener('fetch', (e) => {
        // Just a pass-through for now, enables PWA install prompt
    });
    """
    return Response(sw_code, mimetype='application/javascript')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
