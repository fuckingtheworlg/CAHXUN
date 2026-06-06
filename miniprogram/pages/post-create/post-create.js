const { request } = require('../../utils/request');
const { ensureLogin } = require('../../utils/auth');
const { withTheme } = require('../../utils/theme');
const config = require('../../utils/config');

const CATEGORIES = ['校园生活', '失物招领', '二手交易', '活动通报', '兼职实习', '吐槽求助', '学习交流'];
const MAX_LEN = 500;
const MAX_IMAGES = 9;

Page(withTheme({
  data: {
    content: '',
    category: '',
    submitting: false,
    categories: CATEGORIES,
    maxLen: MAX_LEN,
    length: 0,
    images: [],
    maxImages: MAX_IMAGES,
  },

  onChooseImage() {
    const remain = MAX_IMAGES - this.data.images.length;
    if (remain <= 0) {
      wx.showToast({ title: `最多 ${MAX_IMAGES} 张图片`, icon: 'none' });
      return;
    }
    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: (res) => {
        const newImgs = res.tempFiles.map((f) => ({
          path: f.tempFilePath,
          uploaded: false,
          url: '',
        }));
        this.setData({
          images: this.data.images.concat(newImgs),
        });
      },
    });
  },

  onRemoveImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = this.data.images.slice();
    images.splice(index, 1);
    this.setData({ images });
  },

  onPreviewImage(e) {
    const index = e.currentTarget.dataset.index;
    const urls = this.data.images.map((i) => i.path);
    wx.previewImage({ current: urls[index], urls });
  },

  uploadAll() {
    const pending = this.data.images.filter((i) => !i.uploaded);
    if (pending.length === 0) {
      return Promise.resolve(this.data.images.map((i) => i.url));
    }
    const token = wx.getStorageSync('token');
    let done = 0;
    const total = pending.length;
    wx.showLoading({ title: `上传中 0/${total}`, mask: true });

    const uploadOne = (img, idx) =>
      new Promise((resolve, reject) => {
        wx.uploadFile({
          url: `${config.baseUrl}/upload/image`,
          filePath: img.path,
          name: 'file',
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const data = JSON.parse(res.data);
              if (res.statusCode >= 400) {
                reject(new Error(data.detail || '上传失败'));
                return;
              }
              done += 1;
              wx.showLoading({ title: `上传中 ${done}/${total}`, mask: true });
              resolve(data.url);
            } catch (e) {
              reject(new Error('解析响应失败'));
            }
          },
          fail: (err) => reject(new Error(err.errMsg || '网络错误')),
        });
      });

    return Promise.all(this.data.images.map((img, idx) => {
      if (img.uploaded) return Promise.resolve(img.url);
      return uploadOne(img, idx).then((url) => {
        const key = `images[${idx}]`;
        this.setData({ [`${key}.uploaded`]: true, [`${key}.url`]: url });
        return url;
      });
    }));
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
        return this.uploadAll();
      })
      .then((urls) => {
        wx.showLoading({ title: '发布中...', mask: true });
        return request({
          url: '/posts',
          method: 'POST',
          data: {
            content,
            category: this.data.category,
            images: (urls || []).filter(Boolean).join(','),
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
