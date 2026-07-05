/**
 * AIbounty 语音代理 — 腾讯云函数版
 * ==================================
 * 部署方式：
 *   1. 打开 https://console.cloud.tencent.com/scf
 *   2. 新建云函数 → 自定义创建 → Node.js 18+
 *   3. 粘贴本文件内容到 index.js
 *   4. 环境变量设置：
 *      - BAIDU_APP_ID / BAIDU_API_KEY / BAIDU_SECRET_KEY（百度语音）
 *      - 或 OPENAI_API_KEY（OpenAI Whisper）
 *   5. 触发器 → API网关 → 启用
 *   6. 得到 URL: https://xxx.ap-guangzhou.apigateway.myqcloud.com/voice
 *
 * 前端配置：
 *   将 index.html 中的 /api/voice 改为云函数 URL
 */

// ── 百度 Access Token 缓存 ──
let baiduToken = null;
let baiduTokenExpires = 0;

async function getBaiduToken() {
  if (baiduToken && Date.now() < baiduTokenExpires) return baiduToken;
  const key = process.env.BAIDU_API_KEY;
  const secret = process.env.BAIDU_SECRET_KEY;
  if (!key || !secret) return null;
  try {
    const url = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${key}&client_secret=${secret}`;
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (data.access_token) {
      baiduToken = data.access_token;
      baiduTokenExpires = Date.now() + (data.expires_in - 60) * 1000;
      return baiduToken;
    }
    return null;
  } catch(e) { return null; }
}

// ── 百度语音识别 ──
async function recognizeWithBaidu(audioBase64, audioLen, format) {
  const token = await getBaiduToken();
  if (!token) return null;
  try {
    const res = await fetch('https://vop.baidu.com/server_api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        format: format === 'wav' ? 'wav' : 'pcm',
        rate: 16000, channel: 1, cuid: 'aibounty',
        token: token, speech: audioBase64, len: audioLen
      })
    });
    const data = await res.json();
    if (data.err_no === 0 && data.result && data.result.length) return data.result[0];
    console.error('Baidu error:', data);
    return null;
  } catch(e) { return null; }
}

// ── OpenAI Whisper ──
async function recognizeWithWhisper(audioBuffer, format, lang) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) return null;
  try {
    const boundary = '----FormBoundary' + Math.random().toString(36).slice(2);
    let body = '';
    body += `--${boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n`;
    body += `--${boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\n${lang.slice(0,2)}\r\n`;
    body += `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.${format}"\r\nContent-Type: audio/${format}\r\n\r\n`;
    const buf = Buffer.concat([
      Buffer.from(body, 'utf-8'), audioBuffer,
      Buffer.from(`\r\n--${boundary}--\r\n`, 'utf-8')
    ]);
    const res = await fetch('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
      },
      body: buf
    });
    const data = await res.json();
    return data.text || null;
  } catch(e) { return null; }
}

// ── 云函数入口 ──
exports.main_handler = async (event, context) => {
  // 健康检查
  if (event.path === '/health' || event.httpMethod === 'GET') {
    const backends = [];
    if (process.env.BAIDU_API_KEY) backends.push('baidu');
    if (process.env.OPENAI_API_KEY) backends.push('openai-whisper');
    return {
      isBase64Encoded: false,
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({
        status: 'ok', backends: backends.length ? backends : 'none',
        message: backends.length ? '语音代理就绪' : '未配置语音后端'
      })
    };
  }

  // 语音识别
  if (event.path === '/voice' && event.httpMethod === 'POST') {
    try {
      // 解析 multipart form-data
      const body = Buffer.from(event.body, event.isBase64Encoded ? 'base64' : 'utf-8');
      const ct = event.headers?.['Content-Type'] || event.headers?.['content-type'] || '';
      const boundary = ct.match(/boundary=(.+)/)?.[1];
      if (!boundary) {
        return respond(400, { error: 'Invalid content-type', code: 'NO_BOUNDARY' });
      }

      // 简单解析 multipart
      const parts = body.toString('binary').split(`--${boundary}`);
      let audioBuffer = null;
      let audioFormat = 'wav';
      let lang = 'zh-CN';

      for (const part of parts) {
        if (part.includes('Content-Disposition: form-data; name="audio"') || part.includes('Content-Disposition: form-data; name="file"')) {
          const lines = part.split('\r\n');
          const formatMatch = part.match(/filename="audio\.(\w+)"/);
          if (formatMatch) audioFormat = formatMatch[1];
          const startIdx = part.indexOf('\r\n\r\n') + 4;
          const endIdx = part.lastIndexOf('\r\n--');
          if (endIdx > startIdx) {
            audioBuffer = Buffer.from(part.slice(startIdx, endIdx), 'binary');
          }
        } else if (part.includes('Content-Disposition: form-data; name="lang"')) {
          const m = part.match(/\r\n\r\n(.+)\r\n/);
          if (m) lang = m[1].trim();
        } else if (part.includes('Content-Disposition: form-data; name="format"')) {
          const m = part.match(/\r\n\r\n(.+)\r\n/);
          if (m) audioFormat = m[1].trim();
        }
      }

      if (!audioBuffer) {
        return respond(400, { error: 'No audio file', code: 'NO_AUDIO' });
      }

      // 识别
      let result = null;
      if (process.env.BAIDU_API_KEY) {
        result = await recognizeWithBaidu(audioBuffer.toString('base64'), audioBuffer.length, audioFormat);
      }
      if (!result && process.env.OPENAI_API_KEY) {
        result = await recognizeWithWhisper(audioBuffer, audioFormat, lang);
      }

      if (result) return respond(200, { text: result });

      const available = [];
      if (process.env.BAIDU_API_KEY) available.push('baidu');
      if (process.env.OPENAI_API_KEY) available.push('openai-whisper');
      return respond(503, {
        error: 'Voice backend not configured', code: 'NO_BACKEND',
        message: available.length ? `Configured: ${available.join(', ')}` : 'No backend configured'
      });
    } catch(e) {
      console.error('Voice error:', e);
      return respond(500, { error: 'Internal error', code: 'SERVER_ERROR' });
    }
  }

  return respond(404, { error: 'Not found' });
};

function respond(code, data) {
  return {
    isBase64Encoded: false,
    statusCode: code,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    },
    body: JSON.stringify(data)
  };
}
