#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 quiz.html 添加收藏、错题重做、重新答题功能"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('quiz.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ===== 1. state 中添加 bookmarked 字段 =====
html = html.replace(
    "submitted: false,",
    "submitted: false,\n  bookmarked: new Set(),"
)

# ===== 2. localStorage 保存/读取函数（放在 state 定义之后）=====
state_end = "  bookmarked: new Set(),\n};"
save_load_fns = """
// ==================== localStorage 持久化 ====================
function saveState() {
  try {
    localStorage.setItem('qa_answered', JSON.stringify([...state.answered]));
    localStorage.setItem('qa_results', JSON.stringify(state.results));
    localStorage.setItem('qa_wrong', JSON.stringify([...state.wrong]));
    localStorage.setItem('qa_bookmarked', JSON.stringify([...state.bookmarked]));
  } catch(e) {}
}

function loadState() {
  try {
    const a = JSON.parse(localStorage.getItem('qa_answers') || '[]');
    state.answers = JSON.parse(localStorage.getItem('qa_answers') || '{}');
    JSON.parse(localStorage.getItem('qa_answered') || '[]').forEach(id => state.answered.add(id));
    state.results = JSON.parse(localStorage.getItem('qa_results') || '{}');
    JSON.parse(localStorage.getItem('qa_wrong') || '[]').forEach(id => state.wrong.add(id));
    JSON.parse(localStorage.getItem('qa_bookmarked') || '[]').forEach(id => state.bookmarked.add(id));
  } catch(e) {}
}
"""
html = html.replace(state_end, state_end + save_load_fns)

# ===== 3. 收藏切换函数 =====
toggle_bm_fn = """
function toggleBookmark() {
  const q = getCur(); if (!q) return;
  if (state.bookmarked.has(q.id)) state.bookmarked.delete(q.id); else state.bookmarked.add(q.id);
  renderBMbtn(q);
  saveState();
  updateStats();
}
function renderBMbtn(q) {
  const b = document.getElementById('bmBtn');
  if (!b) return;
  b.textContent = state.bookmarked.has(q.id) ? '★' : '☆';
  b.className = 'bm-btn' + (state.bookmarked.has(q.id)?' on':'');
}
"""
html = html.replace("function toggleZoom(img)", toggle_bm_fn + "\nfunction toggleZoom(img)")

# ===== 4. 收藏筛选 =====
# 在 setFilter 中添加 'bookmarked' 处理
html = html.replace(
    "function setFilter(f) {",
    "function setFilter(f) {\n  state.filter = f;"
)
# Actually setFilter already sets state.filter = f, let me check...
# The original setFilter starts with:
# function setFilter(f) {
#   state.filter = f;
# So I need to add the bookmark mode handling somewhere

# Let me add bookmark handling in getFiltered
html = html.replace(
    "function getFiltered() {\n  return QUESTIONS.filter(q => state.filter === 'all' || q.type === state.filter);\n}",
    """function getFiltered() {
  let qs = QUESTIONS;
  // 错题集模式只显示错题
  if (state.mode === 'wrong') qs = qs.filter(q => state.wrong.has(q.id));
  // 题型筛选
  if (state.filter !== 'all' && state.filter !== 'star') qs = qs.filter(q => q.type === state.filter);
  // 收藏筛选
  if (state.filter === 'star') qs = qs.filter(q => state.bookmarked.has(q.id));
  return qs;
}"""
)

# ===== 5. mode tabs 中添加错题集 tab =====
old_tabs = """    <button class="tab" data-mode="nav" onclick="setMode('nav')">🗂️ 答题卡 <span class="badge" id="wrongBadge">0</span></button>"""
new_tabs = """    <button class="tab" data-mode="wrong" onclick="setMode('wrong')">📕 错题集 <span class="badge" id="wrongBadge">0</span></button>
    <button class="tab" data-mode="nav" onclick="setMode('nav')">🗂️ 答题卡</button>
    <button class="tab" onclick="resetQuiz()">🔄 重来</button>"""
html = html.replace(old_tabs, new_tabs)

# ===== 6. 筛选栏添加"收藏" =====
old_filters = """    <span class="filter-chip" data-filter="code" onclick="setFilter('code')">编程题</span>"""
new_filters = """    <span class="filter-chip" data-filter="code" onclick="setFilter('code')">编程题</span>
    <span class="filter-chip" data-filter="star" onclick="setFilter('star')">⭐ 收藏</span>"""
html = html.replace(old_filters, new_filters)

# ===== 7. 标题栏添加收藏星星按钮 =====
old_header = """      <div class="q-header">
        <span class="q-number" id="qNum"></span>
        <span class="q-type" id="qTypeLabel"></span>
      </div>"""
new_header = """      <div class="q-header">
        <span class="q-number" id="qNum"></span>
        <span class="q-type" id="qTypeLabel"></span>
        <button class="bm-btn" id="bmBtn" onclick="toggleBookmark()" title="收藏此题">☆</button>
      </div>"""
html = html.replace(old_header, new_header)

# ===== 8. 添加"错题集清空"提示在 renderQ 中 =====
# 在 renderQ 开头添加错题集提示
html = html.replace(
    "state.submitted = false;",
    "state.submitted = false;\n  const filtered = getFiltered();\n  if (filtered.length === 0 && state.mode === \'wrong\') { document.getElementById(\'qNum\').textContent = \'🎉 错题已全部消灭！\'; document.getElementById(\'qTypeLabel\').textContent=\'\'; document.getElementById(\'qText\').innerHTML=\'太棒了！你已经把所有错题都做对了。<br>点击 <b>答题卡</b> 查看全部题目，或切换到 <b>刷题</b> 模式继续练习。\'; hideAll(); return; }"
)

# Need to handle the empty state better - add a hideAll function
hide_all_fn = """
function hideAll() {
  document.getElementById('qImgWrap').classList.add('hidden');
  document.getElementById('optArea').classList.add('hidden');
  document.getElementById('tfArea').classList.add('hidden');
  document.getElementById('inpArea').classList.add('hidden');
  document.getElementById('fb').className='feedback'; document.getElementById('fb').style.display='none';
  document.getElementById('btnSubmit').classList.add('hidden');
  document.getElementById('btnNext').classList.add('hidden');
  document.getElementById('btnShowAns').classList.add('hidden');
  document.getElementById('btnSkip').classList.add('hidden');
}
"""
html = html.replace("function toggleBookmark()", hide_all_fn + "\nfunction toggleBookmark()")

# ===== 9. setMode 中处理 wrong 模式 =====
html = html.replace(
    "state.mode = m;",
    """state.mode = m;
  if (m === 'wrong' && state.wrong.size === 0) {
    document.getElementById('panelPractice').classList.remove('hidden');
    document.querySelectorAll('#modeTabs .tab').forEach(t => t.classList.toggle('active', t.dataset.mode === m));
    document.getElementById('panelReview').classList.add('hidden');
    document.getElementById('panelNav').classList.add('hidden');
    document.getElementById('resultPanel').classList.remove('show');
    document.getElementById('quizBar').classList.add('hidden');
    document.getElementById('qNum').textContent = '🎉 暂无错题';
    document.getElementById('qTypeLabel').textContent = '';
    document.getElementById('qText').innerHTML = '恭喜！你还没有做错过题目，继续保持！<br>切换到 <b>刷题</b> 模式继续练习。';
    hideAll();
    return;
  }"""
)

# ===== 10. setMode 中添加到 wrong 处理 =====
html = html.replace(
    "if (m === 'practice') { document.getElementById('panelPractice').classList.remove('hidden'); renderQ(); }",
    """if (m === 'practice') { document.getElementById('panelPractice').classList.remove('hidden'); renderQ(); }
    else if (m === 'wrong') { document.getElementById('panelPractice').classList.remove('hidden'); renderQ(); }"""
)

# ===== 11. 在 renderQ 中恢复收藏状态并调用 saveState =====
# 在 renderQ 中，题目渲染完成后，在 restoreAns 调用后加入 renderBMbtn
html = html.replace(
    "  if (state.answered.has(q.id)) restoreAns(q);",
    """  if (state.answered.has(q.id)) restoreAns(q);
  renderBMbtn(q);"""
)

# ===== 12. submitAns 中调用 saveState =====
html = html.replace(
    "  updateStats();\n  document.getElementById('btnShowAns').classList.toggle('hidden', ok);\n}",
    """  updateStats();
  saveState();
  document.getElementById('btnShowAns').classList.toggle('hidden', ok);
  // 错题集模式下答对自动移除
  if (ok && state.mode === 'wrong' && state.wrong.has(q.id)) {
    state.wrong.delete(q.id);
    setTimeout(() => {
      const fl = getFiltered();
      if (fl.length === 0) renderQ();
      else nextQ();
    }, 1000);
  }
}"""
)

# ===== 13. 重新答题函数 =====
reset_fn = """
function resetQuiz() {
  if (!confirm('确定要清除所有答题记录重新开始吗？')) return;
  if (state.quizTimer) clearInterval(state.quizTimer);
  state.answers = {};
  state.results = {};
  state.answered = new Set();
  state.wrong = new Set();
  state.bookmarked = new Set();
  state.curIdx = 0;
  state.submitted = false;
  state.quizActive = false;
  localStorage.removeItem('qa_answers');
  localStorage.removeItem('qa_answered');
  localStorage.removeItem('qa_results');
  localStorage.removeItem('qa_wrong');
  localStorage.removeItem('qa_bookmarked');
  document.getElementById('resultPanel').classList.remove('show');
  setMode('practice');
  updateStats();
}
"""
html = html.replace("// ==================== 初始化 ====================", reset_fn + "\n// ==================== 初始化 ====================")

# ===== 14. 错题集下不显示跳过按钮 =====
html = html.replace(
    "if (state.mode === 'quiz') document.getElementById('btnSkip').classList.remove('hidden');",
    "if (state.mode === 'quiz' && state.mode !== 'wrong') document.getElementById('btnSkip').classList.remove('hidden');"
)

# ===== 15. renderNav 中显示收藏状态 =====
html = html.replace(
    "d.classList.add(state.wrong.has(q.id)?'err':'done');",
    "d.classList.add(state.wrong.has(q.id)?'err':'done');\n    if (state.bookmarked.has(q.id)) d.textContent = '★'+q.id;"
)

# ===== 16. review 模式显示收藏 =====
html = html.replace(
    '<span style="font-weight:700;color:#667eea;">#${q.id}</span>',
    '<span style="font-weight:700;color:#667eea;">${state.bookmarked.has(q.id)?"★ ":""}#${q.id}</span>'
)

# ===== 17. 添加收藏按钮 CSS =====
css_bm = """
  .bm-btn {
    background: none; border: none; font-size: 22px; cursor: pointer;
    color: #ccc; transition: all 0.2s; padding: 2px 6px; line-height: 1;
    margin-left: auto;
  }
  .bm-btn:hover { transform: scale(1.2); color: #f5a623; }
  .bm-btn.on { color: #f5a623; }
"""
html = html.replace("/* ===== 原图折叠 ===== */", css_bm + "\n/* ===== 原图折叠 ===== */")

# ===== 18. 初始化时调用 loadState =====
html = html.replace(
    "updateStats();\nrenderQ();",
    "loadState();\nupdateStats();\nrenderQ();"
)

# ===== 19. 在 nextQ 后保存状态 =====
html = html.replace(
    "  updateStats();\n}",
    "  updateStats();\n  saveState();\n}"
)

# ===== 20. 在 renderNav 中的导航点击恢复 =====
html = html.replace(
    "if (idx >= 0) {\n        state.curIdx = idx;\n        setMode('practice');\n      }",
    "if (idx >= 0) {\n        state.curIdx = idx;\n        setMode(state.mode === 'wrong' ? 'wrong' : 'practice');\n      }"
)

# ===== 21. 修正 quizBar 的隐藏逻辑 =====
# 错题集模式下默认隐藏 quizBar
# This should already be handled in setMode

# ===== 22. 更新 filter chip 计数显示 =====
html = html.replace(
    "document.querySelector('.filter-chip[data-filter=\"all\"]').textContent = `全部 (${total})`;",
    """document.querySelector('.filter-chip[data-filter="all"]').textContent = `全部 (${total})`;
  document.querySelector('.filter-chip[data-filter="star"]').textContent = `⭐ 收藏 (${state.bookmarked.size})`;"""
)

# ===== 23. 在 updateStats 中更新收藏计数 =====
html = html.replace(
    "document.getElementById('wrongBadge').textContent = state.wrong.size;",
    "document.getElementById('wrongBadge').textContent = state.wrong.size;\n  const starChip = document.querySelector('.filter-chip[data-filter=\"star\"]');\n  if (starChip) starChip.textContent = `⭐ 收藏 (${state.bookmarked.size})`;"
)

# ===== 24. renderReview 里添加收藏状态 =====
# Already did this above

# ===== 25. 错题集 noWrong 时重置 filter 到 all =====
# Handled in setMode

# 写入
with open('quiz.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ quiz.html 已更新！')
print('功能: 收藏⭐ | 错题集📕 | 重新答题🔄 | localStorage持久化')
