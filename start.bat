@echo off
chcp 65001 >nul
title 前端刷题服务器

python3 "%~dp0start_server.py"
pause
