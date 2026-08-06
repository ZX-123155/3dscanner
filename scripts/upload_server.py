"""手机照片上传服务器：手机连同一 WiFi 后浏览器直接传照片到 input/，可一键触发重建

用法:
    conda run -n 3dscanner python scripts/upload_server.py [--port 8000] [--host 0.0.0.0]

手机操作:
    1. 手机连接与电脑相同的 WiFi
    2. 浏览器打开 http://<电脑局域网IP>:8000
    3. 选择照片批量上传（自动存到 input/）
    4. 点"开始重建"按钮，服务器后台启动 pipeline.py
"""
import argparse
import cgi
import json
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
SCRIPT_DIR = PROJECT_ROOT / "scripts"
PIPELINE_CMD = [sys.executable, str(SCRIPT_DIR / "pipeline.py"),
                "--input", str(INPUT_DIR),
                "--output", str(PROJECT_ROOT / "output"),
                "--model", str(PROJECT_ROOT / "models" / "3dgs")]

# 重建任务状态（单例）
_build_state = {"running": False, "log": "", "last_result": ""}


def get_lan_ip() -> str:
    """获取本机局域网 IP（通过 UDP 连接探测，不发真实数据）"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def start_build() -> str:
    """后台启动重建管线，返回状态说明"""
    if _build_state["running"]:
        return "重建正在进行中，请稍候"
    _build_state["running"] = True
    _build_state["log"] = ""

    def _run():
        try:
            proc = subprocess.Popen(
                PIPELINE_CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", cwd=str(PROJECT_ROOT),
            )
            for line in proc.stdout:
                _build_state["log"] += line
                if len(_build_state["log"]) > 200_000:  # 截断日志
                    _build_state["log"] = _build_state["log"][-200_000:]
            proc.wait()
            _build_state["last_result"] = ("成功" if proc.returncode == 0 else f"失败(exit={proc.returncode})")
        finally:
            _build_state["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return "重建已启动，请到页面查看进度"


def save_upload(file_item) -> tuple[int, str]:
    """保存一个上传的文件，返回 (保存数量, 消息)"""
    filename = Path(file_item.filename).name  # 防路径穿越
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        return 0, f"跳过非图片文件: {filename}"
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = INPUT_DIR / filename
    with dest.open("wb") as f:
        while chunk := file_item.file.read(1 << 20):
            f.write(chunk)
    logger.info(f"已保存照片: {dest.name}")
    return 1, f"已保存 {filename}"


def render_page(ip: str, port: int) -> str:
    """渲染上传页面 HTML"""
    state = "running" if _build_state["running"] else "idle"
    result = _build_state["last_result"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>3D 扫描仪 - 照片上传</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 0 auto; padding: 20px; }}
  .card {{ background: #fff; border: 1px solid #ddd; border-radius: 12px; padding: 20px; margin-bottom: 16px; }}
  h1 {{ font-size: 20px; }}
  .ip {{ background: #eef; padding: 8px 12px; border-radius: 8px; font-weight: bold; }}
  button {{ padding: 12px 20px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; }}
  .upload-btn {{ background: #2563eb; color: #fff; }}
  .build-btn {{ background: #16a34a; color: #fff; }}
  #log {{ background: #111; color: #0f0; font-family: monospace; font-size: 12px;
         padding: 12px; border-radius: 8px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; }}
  .status {{ font-weight: bold; margin-top: 8px; }}
</style></head><body>
<h1>📷 3D 扫描仪 · 照片上传</h1>
<div class="card">
  <p>1. 选择照片（可多选，建议 30~150 张环绕照）</p>
  <input type="file" id="files" accept="image/*" multiple>
  <br><br>
  <button class="upload-btn" onclick="upload()">上传照片</button>
  <span id="upmsg"></span>
</div>
<div class="card">
  <p>2. 上传完成后，点击开始重建（COLMAP + 3DGS 全流程）</p>
  <button class="build-btn" id="buildBtn" onclick="startBuild()">开始重建</button>
  <div class="status" id="status">状态: {'重建中' if state=='running' else '空闲'}</div>
</div>
<div class="card"><p>重建日志（自动刷新）</p><div id="log"></div></div>
<script>
async function upload() {{
  const files = document.getElementById('files').files;
  if (!files.length) return alert('请先选择照片');
  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  const r = await fetch('/upload', {{ method: 'POST', body: fd }});
  const j = await r.json();
  document.getElementById('upmsg').textContent = `✔ 成功保存 ${{j.saved}} 张，跳过 ${{j.skipped}} 张`;
}}
async function startBuild() {{
  const r = await fetch('/start', {{ method: 'POST' }});
  const j = await r.json();
  document.getElementById('status').textContent = '状态: ' + j.message;
  refreshLog();
}}
async function refreshLog() {{
  const r = await fetch('/log');
  const j = await r.json();
  document.getElementById('log').textContent = j.log || '(暂无日志)';
  document.getElementById('status').textContent = '状态: ' + (j.running ? '重建中' : '空闲');
  setTimeout(refreshLog, 3000);
}}
refreshLog();
</script></body></html>"""


class UploadHandler(BaseHTTPRequestHandler):
    """HTTP 处理器：首页 / 上传 / 启动重建 / 日志"""

    def _send_json(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/log":
            self._send_json({"log": _build_state["log"], "running": _build_state["running"]})
        elif self.path == "/":
            page = render_page(get_lan_ip(), self.server.server_port)
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/upload":
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                    environ={"REQUEST_METHOD": "POST",
                                             "CONTENT_TYPE": self.headers.get("Content-Type", "")})
            saved = skipped = 0
            msgs = []
            for item in form["files"] if "files" in form else []:
                if not isinstance(item, cgi.FieldStorage):
                    continue
                n, msg = save_upload(item)
                saved += n
                if n == 0:
                    skipped += 1
                msgs.append(msg)
            logger.info(f"上传完成: 保存 {saved} 张, 跳过 {skipped} 张")
            self._send_json({"saved": saved, "skipped": skipped, "messages": msgs})
        elif self.path == "/start":
            msg = start_build()
            self._send_json({"message": msg})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):  # 静默默认访问日志（用 loguru 替代）
        logger.debug(f"HTTP {self.address_string()} {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="手机照片上传服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="端口")
    args = parser.parse_args()

    ip = get_lan_ip()
    logger.info(f"上传服务启动: http://{ip}:{args.port}")
    logger.info(f"照片保存目录: {INPUT_DIR}（不存在会自动创建）")
    logger.warning("若手机无法访问，请检查 Windows 防火墙是否放行该端口")

    server = ThreadingHTTPServer((args.host, args.port), UploadHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
