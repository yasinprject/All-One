from flask import Flask, request, render_template_string
import yt_dlp
import logging
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_direct_video_url(page_url):
    """
    yt-dlp ব্যবহার করে যেকোনো ওয়েবসাইটের ভিডিও থেকে 
    সরাসরি (Direct) এবং সর্বোচ্চ কোয়ালিটির স্ট্রিমিং লিংক বের করার ফাংশন।
    """
    ydl_opts = {
        'format': 'best', # সর্বোচ্চ কোয়ালিটি 
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        # ব্রাউজারের মতো আচরণ করার জন্য User-Agent
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"🔍 Extracting video from: {page_url}")
            info = ydl.extract_info(page_url, download=False)
            
            # যদি সরাসরি URL পাওয়া যায়
            if 'url' in info:
                return info['url'], info.get('title', 'Unknown Video')
            
            # যদি একাধিক ফরম্যাট থাকে, তবে সবচেয়ে ভালোটি নিবে
            elif 'formats' in info and len(info['formats']) > 0:
                best_format = info['formats'][-1]
                return best_format['url'], info.get('title', 'Unknown Video')
                
    except Exception as e:
        logger.error(f"❌ Error extracting URL: {str(e)}")
        return None, None
        
    return None, None

@app.route('/')
def index():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🌐 Universal Ad-Free Player</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    background: #0f172a; color: #f8fafc;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px;
                }
                .container {
                    max-width: 600px; width: 100%; background: #1e293b;
                    border-radius: 16px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                    text-align: center;
                }
                h1 { font-size: 28px; margin-bottom: 10px; color: #38bdf8; }
                .subtitle { color: #94a3b8; margin-bottom: 30px; }
                .url-input input {
                    width: 100%; padding: 15px; background: #0f172a;
                    border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 16px;
                }
                .url-input input:focus { outline: none; border-color: #38bdf8; }
                .url-input button {
                    width: 100%; padding: 15px; margin-top: 15px; background: #0284c7;
                    border: none; border-radius: 8px; color: #fff; font-weight: bold;
                    font-size: 18px; cursor: pointer; transition: background 0.3s;
                }
                .url-input button:hover { background: #0369a1; }
                .hint { color: #64748b; font-size: 13px; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 Universal Web Player</h1>
                <p class="subtitle">যেকোনো ওয়েবসাইটের ভিডিও লিংক পেস্ট করুন (অ্যাড-মুক্ত এবং হাই রেজুলেশন)</p>
                <div class="url-input">
                    <form method="GET" action="/play">
                        <input type="text" name="url" placeholder="Paste any video link here..." required>
                        <button type="submit">▶ Watch Ad-Free</button>
                    </form>
                    <div class="hint">
                        💡 সাপোর্ট করে: বেশিরভাগ স্ট্রিমিং সাইট এবং অ্যাডাল্ট সাইট।
                    </div>
                </div>
            </div>
        </body>
        </html>
    """)

@app.route('/play')
def play_video():
    video_url = request.args.get('url')
    
    if not video_url:
        return "❌ No URL provided", 400
    
    try:
        direct_url, title = get_direct_video_url(video_url)
        
        if direct_url:
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>▶ Playing: {{ title }}</title>
                    <link href="https://vjs.zencdn.net/8.0.0/video-js.css" rel="stylesheet" />
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { background: #000; color: #fff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 20px; }
                        .container { max-width: 1000px; width: 100%; background: #111; border-radius: 12px; padding: 20px; }
                        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
                        h2 { font-size: 18px; color: #38bdf8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                        .video-wrapper { width: 100%; background: #000; border-radius: 8px; overflow: hidden; aspect-ratio: 16/9; }
                        #player { width: 100%; height: 100%; }
                        .back-btn { color: #fff; text-decoration: none; background: #333; padding: 8px 16px; border-radius: 6px; font-size: 14px; }
                        .back-btn:hover { background: #444; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🎬 {{ title }}</h2>
                            <a href="/" class="back-btn">← Back</a>
                        </div>
                        <div class="video-wrapper">
                            <video id="player" class="video-js vjs-default-skin vjs-big-play-centered" controls autoplay preload="auto">
                                <source src="{{ direct_url }}" type="application/x-mpegURL">
                                <source src="{{ direct_url }}" type="video/mp4">
                            </video>
                        </div>
                    </div>
                    
                    <script src="https://vjs.zencdn.net/8.0.0/video.min.js"></script>
                    <script>
                        document.addEventListener('DOMContentLoaded', function() {
                            var player = videojs('player', {
                                fluid: true,
                                html5: { hls: { overrideNative: true } }
                            });
                        });
                    </script>
                </body>
                </html>
            """, direct_url=direct_url, title=title)
        else:
            return render_template_string("""
                <div style="text-align: center; color: white; background: #111; padding: 50px; font-family: sans-serif;">
                    <h2 style="color: #ef4444;">❌ Video Extraction Failed</h2>
                    <p style="color: #888; margin: 20px 0;">এই সাইটটির ভিডিও সাপোর্ট করছে না বা ভিডিওটিতে লগইন/DRM প্রোটেকশন আছে।</p>
                    <a href="/" style="color: #38bdf8; text-decoration: none;">← Go Home</a>
                </div>
            """)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
