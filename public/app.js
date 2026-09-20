/**
 * 【前端逻辑】app.js
 * 职责：页面渲染 + 用户交互 + 通过 fetch 与后端 REST API 通信。
 * 前端只认识 /api/* 接口，完全不关心后端用 SQLite 还是别的数据库、
 * AI 是真实模型还是模拟器 —— 这就是「前后端分离、接口契约优先」。
 */

const chatList = document.getElementById('chat-list');
const input = document.getElementById('msg-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');
const healthBadge = document.getElementById('health-badge');

/** 统一 API 错误处理：把后端 { error: { message } } 转成用户可读提示 */
async function apiFetch(url, options) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data?.error?.message || `请求失败（${res.status}）`);
  }
  return data;
}

/** 防 XSS：用户内容一律走 textContent，不用 innerHTML 拼接 */
function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `msg msg-${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;
  const label = document.createElement('span');
  label.className = 'msg-label';
  label.textContent = role === 'user' ? '我' : 'AI';
  div.append(label, bubble);
  chatList.appendChild(div);
  chatList.scrollTop = chatList.scrollHeight;
  return div;
}

function showError(text) {
  const div = document.createElement('div');
  div.className = 'msg msg-error';
  div.textContent = `⚠️ ${text}`;
  chatList.appendChild(div);
  chatList.scrollTop = chatList.scrollHeight;
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  input.disabled = loading;
  sendBtn.textContent = loading ? 'AI 思考中…' : '发送';
}

/** 加载历史消息（GET /api/messages） */
async function loadHistory() {
  try {
    const { messages } = await apiFetch('/api/messages');
    chatList.innerHTML = '';
    if (messages.length === 0) {
      const tip = document.createElement('div');
      tip.className = 'empty-tip';
      tip.textContent = '暂无对话，发送第一条消息开始体验全链路吧';
      chatList.appendChild(tip);
      return;
    }
    messages.forEach((m) => appendMessage(m.role, m.content));
  } catch (err) {
    showError(err.message);
  }
}

/** 发送消息（POST /api/chat）：前端感知到的「AI 能力」全部来自这个接口 */
async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  appendMessage('user', message);
  input.value = '';
  setLoading(true);

  try {
    const { reply } = await apiFetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    appendMessage('assistant', reply);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
    input.focus();
  }
}

/** 清空历史（DELETE /api/messages） */
async function clearHistory() {
  if (!confirm('确定清空全部对话历史？（会同时删除 SQLite 中的记录）')) return;
  try {
    await apiFetch('/api/messages', { method: 'DELETE' });
    await loadHistory();
  } catch (err) {
    showError(err.message);
  }
}

/** 健康检查（GET /api/health）：顶栏展示后端状态与 AI 模式 */
async function checkHealth() {
  try {
    const { aiMode } = await apiFetch('/api/health');
    healthBadge.textContent = `后端在线 · AI 模式：${aiMode}`;
    healthBadge.className = 'badge badge-ok';
  } catch {
    healthBadge.textContent = '后端未连接';
    healthBadge.className = 'badge badge-down';
  }
}

// 事件绑定
sendBtn.addEventListener('click', sendMessage);
clearBtn.addEventListener('click', clearHistory);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// 初始化
checkHealth();
loadHistory();
