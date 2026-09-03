from flask import Flask, request, jsonify, render_template_string
import yt_dlp
import logging
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_direct_video_url(page_url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
    # সম্পূর্ণ আধুনিক ফ্রন্টএন্ড (HTML, CSS, JS)
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="bn">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Premium Video Player</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <style>
                body { background-color: #0f172a; color: white; -webkit-tap-highlight-color: transparent; }
                .glass { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(10px); border-top: 1px solid rgba(255,255,255,0.1); }
                .hide-controls { opacity: 0; pointer-events: none; }
                .show-controls { opacity: 1; pointer-events: auto; transition: opacity 0.3s ease; }
                input[type=range] { accent-color: #38bdf8; }
                /* Loader */
                .loader { border: 4px solid rgba(255,255,255,0.1); border-left-color: #38bdf8; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body class="h-screen w-screen overflow-hidden flex flex-col">
            
            <!-- Home Screen -->
            <div id="home-screen" class="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col items-center w-full max-w-2xl mx-auto transition-all duration-300">
                <div class="text-center w-full mb-10 mt-10">
                    <h1 class="text-4xl font-bold text-sky-400 mb-2"><i class="fa-solid fa-play-circle"></i> PlayX </h1>
                    <p class="text-slate-400 text-sm">যেকোনো ভিডিও লিংক দিন এবং স্মুথলি উপভোগ করুন</p>
                </div>
                
                <div class="w-full bg-slate-800 p-2 rounded-2xl flex items-center shadow-2xl border border-slate-700 mb-8">
                    <input type="url" id="video-url" placeholder="Paste video link here..." class="w-full bg-transparent border-none outline-none px-4 text-white placeholder-slate-500">
                    <button onclick="extractAndPlay()" class="bg-sky-500 hover:bg-sky-400 text-white px-6 py-3 rounded-xl font-semibold transition-all flex items-center gap-2">
                        <i class="fa-solid fa-play"></i> Play
                    </button>
                </div>

                <!-- History Section -->
                <div class="w-full">
                    <h3 class="text-slate-300 font-semibold mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-clock-rotate-left"></i> Watch History
                    </h3>
                    <div id="history-list" class="space-y-3">
                        <!-- History items will be populated by JS -->
                    </div>
                </div>
            </div>

            <!-- Loading Overlay -->
            <div id="loading-screen" class="hidden fixed inset-0 bg-slate-900/90 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
                <div class="loader mb-4"></div>
                <p class="text-sky-400 font-medium animate-pulse">লিংক প্রসেসিং হচ্ছে, একটু অপেক্ষা করুন...</p>
                <p class="text-slate-500 text-xs mt-2">সার্ভার থেকে ভিডিওর হাই-কোয়ালিটি সোর্স বের করা হচ্ছে</p>
            </div>

            <!-- Video Player Screen -->
            <div id="player-screen" class="hidden fixed inset-0 bg-black z-40 flex items-center justify-center">
                <video id="main-video" class="w-full h-full object-contain" playsinline></video>
                
                <!-- Custom Controls Overlay -->
                <div id="controls-overlay" class="absolute inset-0 flex flex-col justify-between show-controls">
                    
                    <!-- Top Bar -->
                    <div class="glass p-4 flex justify-between items-center bg-gradient-to-b from-black/80 to-transparent">
                        <button onclick="closePlayer()" class="text-white hover:text-sky-400 text-xl px-2"><i class="fa-solid fa-arrow-left"></i></button>
                        <h2 id="video-title" class="text-white text-sm font-medium truncate px-4 max-w-[60%]">Video Title</h2>
                        <button onclick="downloadVideo()" class="text-white hover:text-sky-400 text-xl px-2" title="Download"><i class="fa-solid fa-download"></i></button>
                    </div>

                    <!-- Middle Double Tap Area for 10s skip (Hidden buttons basically) -->
                    <div class="flex-1 flex items-center justify-center gap-20 px-10">
                        <div class="w-1/3 h-full flex items-center justify-center cursor-pointer" ondblclick="skip(-10)"></div>
                        <div class="w-1/3 h-full flex items-center justify-center cursor-pointer" onclick="togglePlay()"></div>
                        <div class="w-1/3 h-full flex items-center justify-center cursor-pointer" ondblclick="skip(10)"></div>
                    </div>

                    <!-- Main Loading Spinner for buffering -->
                    <div id="buffer-loader" class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 hidden">
                        <div class="loader"></div>
                    </div>

                    <!-- Bottom Bar -->
                    <div class="glass p-4 flex flex-col gap-3 bg-gradient-to-t from-black/90 to-transparent">
                        
                        <!-- Timeline -->
                        <div class="flex items-center gap-3 text-xs font-mono text-slate-300">
                            <span id="current-time">00:00</span>
                            <input type="range" id="seek-bar" class="w-full h-1 bg-slate-600 rounded-lg appearance-none cursor-pointer" value="0" step="0.1">
                            <span id="duration">00:00</span>
                        </div>

                        <!-- Controls Row -->
                        <div class="flex justify-between items-center">
                            <div class="flex items-center gap-4">
                                <button onclick="togglePlay()" id="play-btn" class="text-2xl hover:text-sky-400 w-8"><i class="fa-solid fa-play"></i></button>
                                <button onclick="skip(-10)" class="text-lg hover:text-sky-400"><i class="fa-solid fa-rotate-left"></i> <span class="text-[10px] absolute -ml-4 mt-2">10</span></button>
                                <button onclick="skip(10)" class="text-lg hover:text-sky-400"><i class="fa-solid fa-rotate-right"></i> <span class="text-[10px] absolute -ml-4 mt-2">10</span></button>
                            </div>
                            
                            <div class="flex items-center gap-4">
                                <!-- Brightness -->
                                <div class="flex items-center gap-2 group relative">
                                    <i class="fa-solid fa-sun text-sm text-slate-400"></i>
                                    <input type="range" id="brightness-bar" min="20" max="200" value="100" class="w-16 h-1 hidden md:block group-hover:block transition-all">
                                </div>
                                <!-- Volume -->
                                <div class="flex items-center gap-2 group relative">
                                    <i class="fa-solid fa-volume-high text-sm text-slate-400" id="vol-icon"></i>
                                    <input type="range" id="volume-bar" min="0" max="1" step="0.1" value="1" class="w-16 h-1 hidden md:block group-hover:block transition-all">
                                </div>
                                <!-- Fullscreen -->
                                <button onclick="toggleFullScreen()" class="text-xl hover:text-sky-400 ml-2"><i class="fa-solid fa-expand"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Elements
                const video = document.getElementById('main-video');
                const playBtn = document.getElementById('play-btn');
                const seekBar = document.getElementById('seek-bar');
                const volumeBar = document.getElementById('volume-bar');
                const brightnessBar = document.getElementById('brightness-bar');
                const currentTimeEl = document.getElementById('current-time');
                const durationEl = document.getElementById('duration');
                const controlsOverlay = document.getElementById('controls-overlay');
                const bufferLoader = document.getElementById('buffer-loader');
                
                let hls = null;
                let controlsTimeout;
                let currentDownloadUrl = '';

                // API Call for Extracting Link
                async function extractAndPlay(url = null) {
                    const videoUrl = url || document.getElementById('video-url').value;
                    if (!videoUrl) return alert("Please enter a valid URL");

                    document.getElementById('loading-screen').classList.remove('hidden');

                    try {
                        const response = await fetch('/api/extract', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url: videoUrl })
                        });
                        const data = await response.json();

                        if (data.success) {
                            saveHistory(videoUrl, data.title);
                            openPlayer(data.direct_url, data.title);
                        } else {
                            alert("Failed to extract video. The site might be protected.");
                        }
                    } catch (err) {
                        alert("An error occurred connecting to the server.");
                    } finally {
                        document.getElementById('loading-screen').classList.add('hidden');
                    }
                }

                // Initialize Player
                function openPlayer(directUrl, title) {
                    document.getElementById('home-screen').classList.add('hidden');
                    document.getElementById('player-screen').classList.remove('hidden');
                    document.getElementById('video-title').innerText = title;
                    currentDownloadUrl = directUrl;

                    if (Hls.isSupported() && directUrl.includes('.m3u8')) {
                        if(hls) hls.destroy();
                        hls = new Hls();
                        hls.loadSource(directUrl);
                        hls.attachMedia(video);
                        hls.on(Hls.Events.MANIFEST_PARSED, function() { video.play(); });
                    } else {
                        video.src = directUrl;
                        video.play();
                    }
                    resetControlsHideTimer();
                }

                // Close Player
                function closePlayer() {
                    video.pause();
                    video.src = '';
                    if(hls) hls.destroy();
                    document.getElementById('player-screen').classList.add('hidden');
                    document.getElementById('home-screen').classList.remove('hidden');
                    if(document.fullscreenElement) document.exitFullscreen();
                    loadHistory();
                }

                // Play / Pause
                function togglePlay() {
                    if (video.paused) video.play();
                    else video.pause();
                }

                // Update Play/Pause Icon
                video.addEventListener('play', () => playBtn.innerHTML = '<i class="fa-solid fa-pause"></i>');
                video.addEventListener('pause', () => playBtn.innerHTML = '<i class="fa-solid fa-play"></i>');

                // Time Format Helper
                function formatTime(seconds) {
                    if(isNaN(seconds)) return "00:00";
                    const h = Math.floor(seconds / 3600);
                    const m = Math.floor((seconds % 3600) / 60);
                    const s = Math.floor(seconds % 60);
                    if (h > 0) return `${h}:${m < 10 ? '0'+m : m}:${s < 10 ? '0'+s : s}`;
                    return `${m < 10 ? '0'+m : m}:${s < 10 ? '0'+s : s}`;
                }

                // Update Timeline
                video.addEventListener('timeupdate', () => {
                    seekBar.value = (video.currentTime / video.duration) * 100 || 0;
                    currentTimeEl.innerText = formatTime(video.currentTime);
                });
                video.addEventListener('loadedmetadata', () => {
                    durationEl.innerText = formatTime(video.duration);
                });

                // Seek functionality
                seekBar.addEventListener('input', (e) => {
                    const time = (e.target.value / 100) * video.duration;
                    video.currentTime = time;
                });

                // Skip 10s
                function skip(amount) {
                    video.currentTime += amount;
                    resetControlsHideTimer();
                }

                // Volume Control
                volumeBar.addEventListener('input', (e) => {
                    video.volume = e.target.value;
                    const icon = document.getElementById('vol-icon');
                    if(video.volume === 0) icon.className = 'fa-solid fa-volume-xmark text-sm text-slate-400';
                    else if(video.volume < 0.5) icon.className = 'fa-solid fa-volume-low text-sm text-slate-400';
                    else icon.className = 'fa-solid fa-volume-high text-sm text-slate-400';
                });

                // Brightness Control (CSS Filter)
                brightnessBar.addEventListener('input', (e) => {
                    video.style.filter = `brightness(${e.target.value}%)`;
                });

                // Fullscreen
                function toggleFullScreen() {
                    const playerContainer = document.getElementById('player-screen');
                    if (!document.fullscreenElement) {
                        playerContainer.requestFullscreen().catch(err => console.log(err));
                    } else {
                        document.exitFullscreen();
                    }
                }

                // Download functionality
                function downloadVideo() {
                    if(currentDownloadUrl.includes('.m3u8')){
                        alert("⚠️ এটি একটি HLS/M3U8 স্ট্রিমিং ভিডিও। এটি সরাসরি ডাউনলোড সাপোর্ট করে না।");
                    } else {
                        window.open(currentDownloadUrl, '_blank');
                    }
                }

                // Auto hide controls logic
                function resetControlsHideTimer() {
                    controlsOverlay.classList.remove('hide-controls');
                    clearTimeout(controlsTimeout);
                    controlsTimeout = setTimeout(() => {
                        if (!video.paused) {
                            controlsOverlay.classList.add('hide-controls');
                        }
                    }, 3000);
                }
                
                document.getElementById('player-screen').addEventListener('mousemove', resetControlsHideTimer);
                document.getElementById('player-screen').addEventListener('touchstart', resetControlsHideTimer);
                document.getElementById('player-screen').addEventListener('click', resetControlsHideTimer);

                // Buffering visual
                video.addEventListener('waiting', () => bufferLoader.classList.remove('hidden'));
                video.addEventListener('playing', () => bufferLoader.classList.add('hidden'));

                // History Management (LocalStorage)
                function saveHistory(url, title) {
                    let history = JSON.parse(localStorage.getItem('playx_history')) || [];
                    // Remove duplicate
                    history = history.filter(item => item.url !== url);
                    history.unshift({ url, title, date: new Date().toLocaleDateString() });
                    if(history.length > 10) history.pop(); // Keep only last 10
                    localStorage.setItem('playx_history', JSON.stringify(history));
                }

                function loadHistory() {
                    const history = JSON.parse(localStorage.getItem('playx_history')) || [];
                    const list = document.getElementById('history-list');
                    if(history.length === 0){
                        list.innerHTML = '<p class="text-slate-500 text-sm">কোনো হিস্ট্রি পাওয়া যায়নি</p>';
                        return;
                    }
                    list.innerHTML = history.map(item => `
                        <div onclick="extractAndPlay('${item.url}')" class="bg-slate-800 p-3 rounded-lg flex justify-between items-center cursor-pointer hover:bg-slate-700 transition border border-slate-700/50">
                            <div class="overflow-hidden pr-4">
                                <h4 class="text-sm font-medium text-slate-200 truncate">${item.title}</h4>
                                <p class="text-[10px] text-slate-500 truncate mt-1">${item.url}</p>
                            </div>
                            <button class="text-sky-500 p-2 rounded-full hover:bg-slate-600">
                                <i class="fa-solid fa-play"></i>
                            </button>
                        </div>
                    `).join('');
                }

                // Initial Load
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
        
    direct_url, title = get_direct_video_url(video_url)
    
    if direct_url:
        return jsonify({
            "success": True, 
            "direct_url": direct_url, 
            "title": title
        })
    return jsonify({"success": False, "error": "Failed to extract"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
