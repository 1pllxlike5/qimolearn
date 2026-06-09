#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""添加前置更新公告弹窗"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('quiz.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ===== 1. 添加版本常量（放在 state 定义后） =====
version_code = """
const APP_VERSION = '2.0';
const CHANGELOG = [
  {ver:'2.0', title:'收藏、错题集、题库修正', date:'2026-06-09',
   items:[
     '⭐ 收藏功能：点击星星收藏题目，进入收藏夹单独刷',
     '📕 错题集：答错的题自动收录，可重做直到消灭',
     '🔄 重新答题：一键清除所有记录从头开始',
     '💾 数据持久化：刷新或关页面不丢答题记录',
     '📝 题库修正：对照原始文档逐题核对，更新至87题',
   ]},
  {ver:'1.0', title:'初始版本', date:'2026-06-09',
   items:[
     '📚 60道前端期末试题（选择题+判断题+填空题+计算题）',
     '📝 三种模式：刷题、测验、阅读',
     '🔍 题型筛选与答题卡导航',
     '🌐 支持局域网和公网分享',
   ]},
];

function checkVersion() {
  try {
    const lastVer = localStorage.getItem('qa_version') || '';
    if (lastVer !== APP_VERSION) {
      document.getElementById('splashOverlay').classList.add('show');
      renderChangelog();
    }
  } catch(e) {}
}

function renderChangelog() {
  const list = document.getElementById('changelogList');
  list.innerHTML = '';
  CHANGELOG.forEach(c => {
    const div = document.createElement('div');
    div.className = 'cl-item' + (c.ver === APP_VERSION ? ' cl-current' : '');
    let html = '<div class="cl-header"><span class="cl-ver">v' + c.ver + '</span>';
    html += '<span class="cl-title">' + c.title + '</span>';
    html += '<span class="cl-date">' + c.date + '</span></div>';
    html += '<ul class="cl-items">';
    c.items.forEach(item => { html += '<li>' + item + '</li>'; });
    html += '</ul>';
    div.innerHTML = html;
    list.appendChild(div);
  });
}

function dismissSplash() {
  document.getElementById('splashOverlay').classList.remove('show');
  try { localStorage.setItem('qa_version', APP_VERSION); } catch(e) {}
}
"""

# 插入到 APP 状态定义之后
html = html.replace(
    "bookmarked: new Set(),\n};",
    "bookmarked: new Set(),\n};" + version_code
)

# ===== 2. 添加 splash CSS =====
splash_css = """
/* ===== 前置公告弹窗 ===== */
.splash-overlay {
  display: none; position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(4px);
  align-items: center; justify-content: center; padding: 16px;
}
.splash-overlay.show { display: flex; }
.splash-card {
  background: #fff; border-radius: 16px; max-width: 480px; width: 100%;
  max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: splashIn 0.3s ease;
}
@keyframes splashIn {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.splash-head {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff; padding: 24px 24px 20px; border-radius: 16px 16px 0 0;
  text-align: center;
}
.splash-head h2 { font-size: 22px; margin-bottom: 4px; }
.splash-head p { font-size: 13px; opacity: 0.85; }
.splash-body { padding: 16px 20px 20px; }
.cl-item {
  padding: 10px 0; border-bottom: 1px solid #eee;
}
.cl-item:last-child { border-bottom: none; }
.cl-current { background: #f8f9ff; margin: 0 -12px; padding: 10px 12px; border-radius: 8px; }
.cl-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.cl-ver {
  font-weight: 700; font-size: 13px; color: #667eea;
  background: #eef0ff; padding: 1px 8px; border-radius: 4px;
}
.cl-current .cl-ver { background: #667eea; color: #fff; }
.cl-title { font-weight: 600; font-size: 14px; flex: 1; }
.cl-date { font-size: 11px; color: #999; }
.cl-items { margin: 0; padding-left: 18px; }
.cl-items li { font-size: 13px; color: #555; line-height: 1.7; }
.splash-foot { padding: 0 20px 20px; text-align: center; }
.splash-foot .btn { width: 100%; padding: 12px; font-size: 16px; }
"""
html = html.replace("/* ===== 前置公告弹窗 ===== */", "")  # remove placeholder if exists
# Insert before the first CSS comment
html = html.replace("/* ===== 原图折叠 ===== */", splash_css + "\n/* ===== 原图折叠 ===== */")

# ===== 3. 添加 splash HTML =====
splash_html = """  <!-- ===== 前置公告弹窗 ===== -->
  <div class="splash-overlay" id="splashOverlay">
    <div class="splash-card">
      <div class="splash-head">
        <h2>📢 更新公告</h2>
        <p>前端期末复习刷题 · v<span id="splashVer">2.0</span></p>
      </div>
      <div class="splash-body" id="changelogList"></div>
      <div class="splash-foot">
        <button class="btn btn-primary" onclick="dismissSplash()">🚀 开始答题</button>
      </div>
    </div>
  </div>"""

# Insert after <div class="container" id="app">
html = html.replace(
    '<div class="container" id="app">',
    '<div class="container" id="app">\n' + splash_html
)

# ===== 4. 初始化时检查版本 =====
html = html.replace(
    "updateStats();\nrenderQ();",
    "checkVersion();\nupdateStats();\nrenderQ();"
)

# ===== 5. 更新 splash 版本号 =====
html = html.replace(
    '<span id="splashVer">2.0</span>',
    '<span id="splashVer">2.0</span>'
)

with open('quiz.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ quiz.html 已更新！添加了前置更新公告弹窗')
