const { request } = require('./request');

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (!res.code) {
          reject(new Error('wx.login failed'));
          return;
        }
        request({
          url: '/auth/login',
          method: 'POST',
          data: { code: res.code },
        })
          .then((data) => {
            wx.setStorageSync('token', data.token);
            wx.setStorageSync('openid', data.openid);
            resolve(data);
          })
          .catch(reject);
      },
      fail: reject,
    });
  });
}

function ensureLogin() {
  const token = wx.getStorageSync('token');
  if (token) return Promise.resolve(token);
  return login().then((data) => data.token);
}

module.exports = { login, ensureLogin };
