"""手机照片上传服务器：手机连同一 WiFi 后浏览器直接传照片到 input/，可一键触发重建

用法:
    C:\\Users\\luyicheng\\miniconda3\\envs\\3dscanner\\python.exe scripts/upload_server.py [--port 8000]

手机操作:
    1. 手机连接与电脑相同的 WiFi
    2. 浏览器打开 http://<电脑局域网IP>:8000
    3. 连续拍照/选图（页面自动积累），拍完点"上传全部"
    4. 点"开始重建"按钮，服务器后台启动 pipeline.py
"""
import argparse
import json
import re
import socket
import subprocess
import sys
import threading
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


def next_img_number() -> int:
    """返回下一个 img_ 序号（扫描现有文件最大编号 +1）"""
    max_n = 0
    if INPUT_DIR.exists():
        for p in INPUT_DIR.iterdir():
            m = re.fullmatch(r"img_(\d+)\.[a-zA-Z0-9]+", p.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def save_upload(filename: str, data: bytes) -> tuple[int, str]:
    """保存上传文件，统一命名为 img_001.jpg / img_002.jpg（顺序编号，绝不覆盖）"""
    safe_name = Path(filename).name  # 防路径穿越
    if not safe_name.lower().endswith((".jpg", ".jpeg", ".png")):
        return 0, f"跳过非图片文件: {safe_name}"
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(safe_name).suffix.lower().replace("jpeg", "jpg")
    dest = INPUT_DIR / f"img_{next_img_number():03d}{ext}"
    dest.write_bytes(data)
    logger.info(f"已保存照片: {dest.name} ({len(data)/1e6:.1f} MB)")
    return 1, f"已保存 {dest.name}"


def count_photos() -> int:
    """统计 input/ 目录已有照片数"""
    if not INPUT_DIR.exists():
        return 0
    return sum(1 for p in INPUT_DIR.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def parse_multipart(header: str, body: bytes) -> list[tuple[str, bytes]]:
    """手写 multipart/form-data 解析，返回 [(filename, data), ...]（不依赖 cgi，支持任意大小）"""
    m = re.search(r'boundary="?([^";]+)"?', header)
    if not m:
        return []
    boundary = ("--" + m.group(1)).encode("utf-8")
    parts = body.split(boundary)
    files = []
    for part in parts:
        # 跳过头部空段和结尾
        if part in (b"", b"--", b"--\r\n") or part.startswith(b"--"):
            continue
        head, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        if content.endswith(b"\r\n"):
            content = content[:-2]
        head_text = head.decode("utf-8", errors="ignore")
        fm = re.search(r'filename="([^"]*)"', head_text)
        if not fm:  # 只处理文件字段，忽略普通表单字段
            continue
        files.append((fm.group(1), content))
    return files


def render_page(ip: str, port: int, photo_count: int) -> str:
    """渲染上传页面 HTML：拍照/选图积累 → 统一上传"""
    state = "running" if _build_state["running"] else "idle"
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
  .cam-btn {{ background: #2563eb; color: #fff; }}
  .pick-btn {{ background: #7c3aed; color: #fff; }}
  .upload-btn {{ background: #16a34a; color: #fff; }}
  .build-btn {{ background: #ea580c; color: #fff; }}
  #log {{ background: #111; color: #0f0; font-family: monospace; font-size: 12px;
         padding: 12px; border-radius: 8px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; }}
  .status {{ font-weight: bold; margin-top: 8px; }}
  #queue {{ margin-top: 12px; }}
  .qitem {{ display: inline-block; margin: 4px; position: relative; }}
  .qitem img {{ width: 72px; height: 72px; object-fit: cover; border-radius: 8px; }}
  .qitem span {{ position: absolute; top: -6px; right: -6px; background: #ef4444; color: #fff;
                border-radius: 50%; width: 18px; height: 18px; text-align: center; font-size: 12px; cursor: pointer; }}
  .hint {{ color: #666; font-size: 13px; }}
</style></head><body>
<h1>📷 3D 扫描仪 · 照片上传</h1>
<div class="card">
  <p><b>第一步：拍照或选图</b>（连续拍，照片会积累在下方列表，最后一起上传）</p>
  <button class="cam-btn" onclick="document.getElementById('camInput').click()">📸 拍照</button>
  <button class="pick-btn" onclick="document.getElementById('pickInput').click()">🖼 从相册多选</button>
  <input type="file" id="camInput" accept="image/*" capture="environment" style="display:none" onchange="queueFiles(this.files); this.value=''">
  <input type="file" id="pickInput" accept="image/*" multiple style="display:none" onchange="queueFiles(this.files); this.value=''">
  <div id="queue"></div>
  <p class="hint" id="qcount">已积累 0 张</p>
</div>
<div class="card">
  <p><b>第二步：统一上传</b>（照片越多重建越好，建议 30~150 张）</p>
  <button class="upload-btn" onclick="uploadAll()">⬆ 上传全部</button>
  <span id="upmsg"></span>
  <p class="hint" id="have">电脑 input/ 现有 {photo_count} 张照片</p>
</div>
<div class="card">
  <p><b>第三步：开始重建</b>（COLMAP + 3DGS 全流程）</p>
  <button class="build-btn" id="buildBtn" onclick="startBuild()">🚀 开始重建</button>
  <div class="status" id="status">状态: {'重建中' if state=='running' else '空闲'}</div>
</div>
<div class="card"><p>重建日志（自动刷新）</p><div id="log"></div></div>
<script>
let queue = [];
function queueFiles(files) {{
  for (const f of files) queue.push(f);
  renderQueue();
}}
function renderQueue() {{
  const box = document.getElementById('queue');
  box.innerHTML = '';
  queue.forEach((f, i) => {{
    const d = document.createElement('div');
    d.className = 'qitem';
    d.innerHTML = `<img src="${{URL.createObjectURL(f)}}"><span onclick="removeQ(${{i}})">×</span>`;
    box.appendChild(d);
  }});
  document.getElementById('qcount').textContent = `已积累 ${{queue.length}} 张，共 ${{(queue.reduce((s,f)=>s+f.size,0)/1e6).toFixed(1)}} MB`;
}}
function removeQ(i) {{ queue.splice(i, 1); renderQueue(); }}
async function uploadAll() {{
  if (!queue.length) return alert('请先拍照或选择照片');
  const fd = new FormData();
  for (const f of queue) fd.append('files', f);
  const btn = document.querySelector('.upload-btn');
  btn.textContent = '上传中...'; btn.disabled = true;
  try {{
    const r = await fetch('/upload', {{ method: 'POST', body: fd }});
    const j = await r.json();
    document.getElementById('upmsg').textContent = `✔ 成功保存 ${{j.saved}} 张，跳过 ${{j.skipped}} 张`;
    queue = []; renderQueue();
    refreshCount();
  }} catch (e) {{ document.getElementById('upmsg').textContent = '✘ 上传失败: ' + e; }}
  btn.textContent = '⬆ 上传全部'; btn.disabled = false;
}}
async function startBuild() {{
  const r = await fetch('/start', {{ method: 'POST' }});
  const j = await r.json();
  document.getElementById('status').textContent = '状态: ' + j.message;
  refreshLog();
}}
async function refreshCount() {{
  try {{
    const r = await fetch('/count');
    const j = await r.json();
    document.getElementById('have').textContent = '电脑 input/ 现有 ' + j.count + ' 张照片';
  }} catch (e) {{}}
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

    def _read_body(self) -> bytes:
        """读取请求体（支持 Content-Length 与 chunked 两种编码）"""
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            chunks = []
            while True:
                line = self.rfile.readline().strip()
                try:
                    size = int(line, 16)
                except ValueError:
                    break
                if size == 0:
                    self.rfile.readline()
                    break
                chunks.append(self.rfile.read(size))
                self.rfile.readline()
            return b"".join(chunks)
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length > 0 else b""

    def do_GET(self):
        if self.path == "/log":
            self._send_json({"log": _build_state["log"], "running": _build_state["running"]})
        elif self.path == "/count":
            self._send_json({"count": count_photos()})
        elif self.path == "/":
            page = render_page(get_lan_ip(), self.server.server_port, count_photos())
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
            body = self._read_body()
            files = parse_multipart(self.headers.get("Content-Type", ""), body)
            saved = skipped = 0
            msgs = []
            for filename, data in files:
                n, msg = save_upload(filename, data)
                saved += n
                skipped += 1 if n == 0 else 0
                msgs.append(msg)
            logger.info(f"上传完成: {len(files)} 个文件, 保存 {saved} 张, 跳过 {skipped} 张")
            self._send_json({"saved": saved, "skipped": skipped, "messages": msgs})
        elif self.path == "/start":
            self._send_json({"message": start_build()})
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
    logger.info(f"照片保存目录: {INPUT_DIR}（已存 {count_photos()} 张）")
    logger.warning("若手机无法访问，请检查 Windows 防火墙是否放行该端口")

    server = ThreadingHTTPServer((args.host, args.port), UploadHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
