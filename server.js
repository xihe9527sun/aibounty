/**
 * AIbounty 语音代理服务器
 * ========================
 * 功能：
 *   1. 托管 site/ 目录下的静态文件（index.html, data.json 等）
 *   2. 提供 /api/voice 端点：接收音频 → 调语音识别API → 返回文字
 *   3. 支持双后端：百度语音 + OpenAI Whisper
 *
 * 用法：
 *   set BAIDU_APP_ID=xxx & set BAIDU_API_KEY=xxx & set BAIDU_SECRET_KEY=xxx
 *   (或 set OPENAI_API_KEY=sk-xxx)
 *   node server.js
 *
 * 前端语音降级流程：
 *   Web Speech API → /api/voice 代理 → 手动输入
 */

const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 5 * 1024 * 1024 } });

// ── 静态文件托管 ──
const staticDir = path.join(__dirname, 'site');
app.use(express.static(staticDir));
// SPA 支持：所有非 API 路由返回 index.html
app.get(/^\/(?!api\/).*/, (req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'));
});

// ── 百度语音 Access Token 缓存 ──
const BAIDU_APP_ID = process.env.BAIDU_APP_ID || '';
const BAIDU_API_KEY = process.env.BAIDU_API_KEY || '';
const BAIDU_SECRET_KEY = process.env.BAIDU_SECRET_KEY || '';
let baiduToken = null;
let baiduTokenExpires = 0;

async function getBaiduToken() {
  if (baiduToken && Date.now() < baiduTokenExpires) return baiduToken;
  if (!BAIDU_API_KEY || !BAIDU_SECRET_KEY) return null;
  try {
    const url = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${BAIDU_API_KEY}&client_secret=${BAIDU_SECRET_KEY}`;
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (data.access_token) {
      baiduToken = data.access_token;
      baiduTokenExpires = Date.now() + (data.expires_in - 60) * 1000;
      return baiduToken;
    }
    console.error('百度 token 获取失败:', data);
    return null;
  } catch (e) {
    console.error('百度 token 请求异常:', e.message);
    return null;
  }
}

// ── 语音识别端点 ──
app.post('/api/voice', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: '未收到音频文件', code: 'NO_AUDIO' });
    }
    const audioBuffer = req.file.buffer;
    const audioFormat = req.body.format || 'wav';
    const lang = req.body.lang || 'zh-CN';

    // 尝试后端：百度 > OpenAI Whisper
    let result = null;

    // 后端1：百度语音识别
    if (BAIDU_API_KEY && BAIDU_SECRET_KEY) {
      result = await recognizeWithBaidu(audioBuffer, audioFormat, lang);
    }

    // 后端2：OpenAI Whisper（百度失败或无百度配置时）
    if (!result && process.env.OPENAI_API_KEY) {
      result = await recognizeWithWhisper(audioBuffer, lang);
    }

    if (result) {
      return res.json({ text: result });
    }

    // 所有后端均不可用
    const available = [];
    if (BAIDU_API_KEY) available.push('百度语音');
    if (process.env.OPENAI_API_KEY) available.push('OpenAI Whisper');
    return res.status(503).json({
      error: '语音识别服务未配置',
      code: 'NO_BACKEND',
      available: available.length ? `已配置: ${available.join(', ')}` : '未配置任何后端，请设置环境变量'
    });
  } catch (e) {
    console.error('语音识别出错:', e);
    res.status(500).json({ error: '语音识别服务异常', code: 'SERVER_ERROR' });
  }
});

// ── 百度语音识别 ──
async function recognizeWithBaidu(audioBuffer, format, lang) {
  const token = await getBaiduToken();
  if (!token) return null;
  try {
    // 百度语音 REST API (短语音)
    const base64 = audioBuffer.toString('base64');
    const body = {
      format: format === 'wav' ? 'wav' : 'pcm',
      rate: 16000,
      channel: 1,
      cuid: 'aibounty',
      token: token,
      speech: base64,
      len: audioBuffer.length
    };
    const res = await fetch('https://vop.baidu.com/server_api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.err_no === 0 && data.result && data.result.length) {
      return data.result[0];
    }
    console.error('百度语音识别失败:', data);
    return null;
  } catch (e) {
    console.error('百度语音请求异常:', e.message);
    return null;
  }
}

// ── OpenAI Whisper 识别 ──
async function recognizeWithWhisper(audioBuffer, lang) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) return null;
  try {
    // 构造 multipart/form-data 请求
    const boundary = '----FormBoundary' + Math.random().toString(36).slice(2);
    let body = '';
    body += `--${boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n`;
    body += `--${boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\n${lang.slice(0,2)}\r\n`;
    body += `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.${format}"\r\nContent-Type: audio/${format}\r\n\r\n`;
    const bodyBuffer = Buffer.concat([
      Buffer.from(body, 'utf-8'),
      audioBuffer,
      Buffer.from(`\r\n--${boundary}--\r\n`, 'utf-8')
    ]);
    const res = await fetch('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': bodyBuffer.length.toString()
      },
      body: bodyBuffer
    });
    const data = await res.json();
    if (data.text) return data.text;
    console.error('Whisper 识别失败:', data);
    return null;
  } catch (e) {
    console.error('Whisper 请求异常:', e.message);
    return null;
  }
}

// ── 健康检查 ──
app.get('/api/health', (req, res) => {
  const backends = [];
  if (BAIDU_API_KEY) backends.push('baidu');
  if (process.env.OPENAI_API_KEY) backends.push('openai-whisper');
  res.json({
    status: 'ok',
    backends: backends.length ? backends : 'none',
    message: backends.length ? '语音代理就绪' : '未配置语音后端，设置环境变量启用'
  });
});

// ── 启动 ──
app.listen(PORT, () => {
  console.log(`\n  🏴‍☠️  AIbounty 服务器已启动`);
  console.log(`  📡  地址: http://localhost:${PORT}`);
  console.log(`  🎤  语音代理: http://localhost:${PORT}/api/voice`);
  console.log(`  💚  健康检查: http://localhost:${PORT}/api/health`);
  const backends = [];
  if (BAIDU_API_KEY) backends.push('百度语音');
  if (process.env.OPENAI_API_KEY) backends.push('OpenAI Whisper');
  if (backends.length) {
    console.log(`  ✅  语音后端已配置: ${backends.join(', ')}`);
  } else {
    console.log(`  ⚠️  未配置语音后端!`);
    console.log(`  💡  设置环境变量启用:`);
    console.log(`      BAIDU_APP_ID + BAIDU_API_KEY + BAIDU_SECRET_KEY (百度)`);
    console.log(`      或 OPENAI_API_KEY (OpenAI Whisper)`);
  }
  console.log(`  📁  静态目录: ${staticDir}\n`);
});
