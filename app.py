#!/usr/bin/env python3

from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "YT-Downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load HTML and CSS (stored in the same directory)
with open("index.html", "r", encoding="utf-8") as f:
    PAGE_HTML = f.read()
with open("style.css", "r", encoding="utf-8") as f:
    STYLE = f"<style>{f.read()}</style>"

@app.route("/")
def index():
    return render_template_string(PAGE_HTML.replace("<!--STYLE-->", STYLE))

@app.route("/get_formats", methods=["POST"])
def get_formats():
    video_url = request.form["url"]
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
        formats = info.get('formats', [])
        video_formats = [
            {"id": f["format_id"], "resolution": f.get("format_note", ""), "ext": f["ext"]}
            for f in formats if f.get("vcodec") != "none" and f.get("acodec") != "none"
        ]
        audio_formats = [
            {"id": f["format_id"], "bitrate": f.get("abr", ""), "ext": f["ext"]}
            for f in formats if f.get("vcodec") == "none"
        ]
        return jsonify({"title": info["title"], "video_formats": video_formats, "audio_formats": audio_formats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["POST"])
def download():
    video_url = request.form["url"]
    format_id = request.form["format_id"]
    file_type = request.form["type"]

    outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        'format': format_id,
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4' if file_type == "video" else None,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
        filepath = os.path.abspath(filename)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return f"Error during download: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
