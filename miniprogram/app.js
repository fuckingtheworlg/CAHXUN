const { login } = require('./utils/auth');
const { getCurrent } = require('./utils/theme');

App({
  onLaunch() {
    this.globalData.theme = getCurrent();
    this.autoLogin();
  },

  autoLogin() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.isLoggedIn = true;
      return;
    }
    login()
      .then(() => {
        this.globalData.isLoggedIn = true;
      })
      .catch((err) => {
        console.warn('Auto login skipped:', err.message || err);
        this.globalData.isLoggedIn = false;
      });
  },

  globalData: {
    isLoggedIn: false,
    theme: 'vibrant',
  },
});
