const config = require('./config');

function getToken() {
  return wx.getStorageSync('token') || '';
}

function request(options) {
  return new Promise((resolve, reject) => {
    const { url, method = 'GET', data, header = {} } = options;
    const token = getToken();
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }

    wx.request({
      url: `${config.baseUrl}${url}`,
      method,
      data,
      timeout: 10000,
      header: {
        'Content-Type': 'application/json',
        ...header,
      },
      success(res) {
        if (res.statusCode === 401) {
          wx.removeStorageSync('token');
          wx.removeStorageSync('openid');
          wx.showToast({ title: '请重新登录', icon: 'none' });
          reject(new Error('Unauthorized'));
          return;
        }
        if (res.statusCode === 429) {
          wx.showToast({ title: '操作太频繁，请稍后再试', icon: 'none' });
          reject(new Error('Rate limited'));
          return;
        }
        if (res.statusCode >= 400) {
          const msg = (res.data && res.data.detail) || '请求失败';
          wx.showToast({ title: msg, icon: 'none' });
          reject(new Error(msg));
          return;
        }
        resolve(res.data);
      },
      fail(err) {
        console.warn('Request failed:', url, err);
        reject(err);
      },
    });
  });
}

function streamRequest(options, onChunk, onDone) {
  const { url, data, header = {} } = options;
  const token = getToken();
  if (token) {
    header['Authorization'] = `Bearer ${token}`;
  }

  const task = wx.request({
    url: `${config.baseUrl}${url}`,
    method: 'POST',
    data,
    enableChunked: true,
    header: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...header,
    },
    success() {
      if (onDone) onDone();
    },
    fail(err) {
      wx.showToast({ title: '网络异常', icon: 'none' });
      if (onDone) onDone(err);
    },
  });

  let buffer = '';
  task.onChunkReceived(function (res) {
    const text = arrayBufferToString(res.data);
    buffer += text;

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data:')) continue;
      const payload = trimmed.slice(5).trim();
      if (payload === '[DONE]') {
        if (onDone) onDone();
        return;
      }
      try {
        const parsed = JSON.parse(payload);
        if (parsed.content && onChunk) {
          onChunk(parsed.content, parsed);
        } else if (parsed.sources && onChunk) {
          onChunk('', parsed);
        }
      } catch (e) {
        // skip malformed chunk
      }
    }
  });

  return task;
}

function arrayBufferToString(buffer) {
  const bytes = new Uint8Array(buffer);
  let result = '';
  for (let i = 0; i < bytes.length; i++) {
    result += String.fromCharCode(bytes[i]);
  }
  try {
    return decodeURIComponent(escape(result));
  } catch (e) {
    return result;
  }
}

module.exports = { request, streamRequest };
