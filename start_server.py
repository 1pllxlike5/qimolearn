#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
刷题服务器 - 启动后手机/电脑可通过浏览器访问

用法:
  python start_server.py          # 仅局域网 (同一WiFi)
  python start_server.py --remote  # 公网访问 (不同网络也能连)
"""
import http.server
import socket
import sys
import os
import threading
import subprocess
import signal
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))
REMOTE = '--remote' in sys.argv
tunnel_process = None

def get_local_ip():
    """获取本机局域网IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
    finally:
        s.close()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, format, *args):
        sys.stdout.write('  >> %s %s %s\n' % (args[0], args[1], args[2]))
        sys.stdout.flush()

def start_tunnel():
    """通过 localhost.run 创建公网隧道"""
    global tunnel_process
    print('  >> 正在创建公网隧道，请稍候...')
    print()

    try:
        tunnel_process = subprocess.Popen(
            ['ssh', '-o', 'StrictHostKeyChecking=no',
                    '-o', 'ServerAliveInterval=30',
                    '-R', f'80:localhost:{PORT}',
                    'nokey@localhost.run'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 读取输出直到获取公网URL
        url = None
        for line in tunnel_process.stdout:
            line = line.strip()
            if line.endswith('.lhr.life') and 'tunneled' in line:
                # 提取 URL
                parts = line.split()
                for p in parts:
                    if p.startswith('https://') and 'lhr.life' in p:
                        url = p
                        break
            if url:
                # 继续读取几行让隧道稳定
                time.sleep(0.5)
                break

        if url:
            print('=' * 55)
            print('  [刷题服务器] 前端期末复习 - 隧道已建立!')
            print('=' * 55)
            print()
            print('  >> 公网地址 (任何网络都能访问):')
            print('     ' + url)
            print()
            print('  >> 将此链接发给同学即可刷题!')
            print()
            print('  >> 本机局域网地址 (同一WiFi下):')
            print('     http://' + get_local_ip() + ':' + str(PORT))
            print()
            print('  >> 按 Ctrl+C 停止服务器')
            print('=' * 55)
        else:
            print('  [!] 未能获取公网地址，请检查网络或重试')
            print()

        # 持续读取输出（保持隧道连接）
        for line in tunnel_process.stdout:
            line = line.strip()
            if line:
                sys.stdout.write('  [tunnel] ' + line + '\n')
                sys.stdout.flush()

    except FileNotFoundError:
        print('  [!] 错误: 未找到 ssh 命令')
        print('  [!] Windows 10/11 请安装 OpenSSH 客户端:')
        print('      设置 > 应用 > 可选功能 > 添加 OpenSSH 客户端')
        print()
    except Exception as e:
        print('  [!] 隧道创建失败:', str(e))
        print()

def cleanup(signum=None, frame=None):
    """退出时清理"""
    global tunnel_process
    if tunnel_process:
        print('\n  >> 正在关闭隧道...')
        tunnel_process.terminate()
        tunnel_process.wait(timeout=3)
    print('  >> 服务器已停止')
    sys.exit(0)

def main():
    global tunnel_process
    os.chdir(DIR)

    # 注册退出清理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 如果是 --remote 模式，在单独线程中启动隧道
    if REMOTE:
        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()
        time.sleep(2)  # 给隧道一点启动时间

    ip = get_local_ip()

    if not REMOTE:
        print('=' * 55)
        print('  [刷题服务器] 前端期末复习 - 已启动!')
        print('=' * 55)
        print()
        print('  手机访问 (确保在同一WiFi下):')
        print('    http://' + ip + ':' + str(PORT))
        print()
        print('  本机访问:')
        print('    http://localhost:' + str(PORT))
        print('    http://127.0.0.1:' + str(PORT))
        print()
        print('  按 Ctrl+C 停止服务器')
        print('=' * 55)
        print()

    # 启动 HTTP 服务器
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        cleanup()

if __name__ == '__main__':
    main()
