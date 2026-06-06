const { request } = require('../../utils/request');
const { ensureLogin } = require('../../utils/auth');
const { withTheme } = require('../../utils/theme');

const CATEGORIES = ['校园生活', '失物招领', '二手交易', '活动通报', '兼职实习', '吐槽求助', '学习交流'];
const MAX_LEN = 500;

Page(withTheme({
  data: {
    content: '',
    category: '',
    submitting: false,
    categories: CATEGORIES,
    maxLen: MAX_LEN,
    length: 0,
  },

  onInput(e) {
    const val = e.detail.value || '';
    this.setData({ content: val, length: val.length });
  },

  onSelectCategory(e) {
    const cat = e.currentTarget.dataset.cat;
    this.setData({ category: this.data.category === cat ? '' : cat });
  },

  onSubmit() {
    if (this.data.submitting) return;
    const content = this.data.content.trim();
    if (content.length < 2) {
      wx.showToast({ title: '内容至少 2 个字', icon: 'none' });
      return;
    }
    if (content.length > MAX_LEN) {
      wx.showToast({ title: `内容不能超过 ${MAX_LEN} 字`, icon: 'none' });
      return;
    }

    ensureLogin()
      .then(() => {
        this.setData({ submitting: true });
        wx.showLoading({ title: '发布中...', mask: true });
        return request({
          url: '/posts',
          method: 'POST',
          data: {
            content,
            category: this.data.category,
          },
        });
      })
      .then(() => {
        wx.hideLoading();
        wx.showToast({ title: '发布成功！', icon: 'success' });
        this.setData({ submitting: false });
        const app = getApp();
        if (app && app.globalData) {
          app.globalData.needRefreshIndex = true;
        }
        setTimeout(() => {
          wx.navigateBack();
        }, 800);
      })
      .catch((err) => {
        wx.hideLoading();
        this.setData({ submitting: false });
        wx.showToast({
          title: (err && err.message) || '发布失败',
          icon: 'none',
          duration: 2000,
        });
      });
  },

  onCancel() {
    if (this.data.content.trim()) {
      wx.showModal({
        title: '确认放弃',
        content: '当前编辑的内容还没保存，确定要离开吗？',
        success: (res) => {
          if (res.confirm) wx.navigateBack();
        },
      });
    } else {
      wx.navigateBack();
    }
  },
}));
