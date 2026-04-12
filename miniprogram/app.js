const { login } = require('./utils/auth');

App({
  onLaunch() {
    this.autoLogin();
  },

  autoLogin() {
    const token = wx.getStorageSync('token');
    if (!token) {
      login().catch((err) => {
        console.warn('Auto login failed:', err);
      });
    }
  },

  globalData: {},
});
