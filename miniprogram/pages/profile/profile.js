const defaultAvatar = '/assets/tab-profile.png';

const genderOptions = ['未设置', '男', '女'];
const gradeOptions = ['未设置', '大一', '大二', '大三', '大四', '研一', '研二', '研三', '博士'];

Page({
  data: {
    avatarUrl: defaultAvatar,
    nickname: '微信用户',
    openidShort: '***',
    gender: 0,
    genderText: '未设置',
    college: '',
    grade: '',
    searchCount: 0,
    chatCount: 0,
    cacheSize: '0 KB',
    showNicknameModal: false,
    nicknameInput: '',
  },

  onShow() {
    this.loadProfile();
    this.calcCache();
    this.loadStats();
  },

  loadProfile() {
    const profile = wx.getStorageSync('userProfile') || {};
    const openid = wx.getStorageSync('openid') || '';
    let openidShort = '***';
    if (openid.length > 8) {
      openidShort = openid.slice(0, 4) + '***' + openid.slice(-4);
    }

    this.setData({
      avatarUrl: profile.avatarUrl || defaultAvatar,
      nickname: profile.nickname || '微信用户',
      gender: profile.gender || 0,
      genderText: genderOptions[profile.gender || 0],
      college: profile.college || '',
      grade: profile.grade || '',
      openidShort,
    });
  },

  saveProfile(updates) {
    const profile = wx.getStorageSync('userProfile') || {};
    const newProfile = { ...profile, ...updates };
    wx.setStorageSync('userProfile', newProfile);
    this.loadProfile();
  },

  loadStats() {
    const searchCount = wx.getStorageSync('stat_search') || 0;
    const chatCount = wx.getStorageSync('stat_chat') || 0;
    this.setData({ searchCount, chatCount });
  },

  // ─── Avatar ───
  onChangeAvatar() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempPath = res.tempFiles[0].tempFilePath;
        this.setData({ avatarUrl: tempPath });
        this.saveProfile({ avatarUrl: tempPath });
        wx.showToast({ title: '头像已更新', icon: 'success' });
      },
    });
  },

  // ─── Nickname ───
  onEditNickname() {
    this.setData({
      showNicknameModal: true,
      nicknameInput: this.data.nickname === '微信用户' ? '' : this.data.nickname,
    });
  },

  onNicknameInput(e) {
    this.setData({ nicknameInput: e.detail.value });
  },

  closeNicknameModal() {
    this.setData({ showNicknameModal: false });
  },

  confirmNickname() {
    const name = this.data.nicknameInput.trim();
    if (!name) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' });
      return;
    }
    this.saveProfile({ nickname: name });
    this.setData({ showNicknameModal: false });
    wx.showToast({ title: '昵称已更新', icon: 'success' });
  },

  // ─── Gender ───
  onEditGender() {
    wx.showActionSheet({
      itemList: ['男', '女'],
      success: (res) => {
        const gender = res.tapIndex + 1;
        this.saveProfile({ gender });
      },
    });
  },

  // ─── College ───
  onEditCollege() {
    const that = this;
    wx.showModal({
      title: '设置学院',
      editable: true,
      placeholderText: '请输入学院名称',
      content: this.data.college || '',
      success(res) {
        if (res.confirm && res.content !== undefined) {
          that.saveProfile({ college: res.content.trim() });
          wx.showToast({ title: '已更新', icon: 'success' });
        }
      },
    });
  },

  // ─── Grade ───
  onEditGrade() {
    wx.showActionSheet({
      itemList: gradeOptions.slice(1),
      success: (res) => {
        this.saveProfile({ grade: gradeOptions[res.tapIndex + 1] });
      },
    });
  },

  // ─── Cache ───
  calcCache() {
    try {
      const info = wx.getStorageInfoSync();
      const kb = info.currentSize || 0;
      const sizeStr = kb < 1024 ? kb + ' KB' : (kb / 1024).toFixed(1) + ' MB';
      this.setData({ cacheSize: sizeStr });
    } catch (e) {
      this.setData({ cacheSize: '未知' });
    }
  },

  onClearCache() {
    wx.showModal({
      title: '清除缓存',
      content: '将清除本地缓存数据（不影响账号信息），确定继续？',
      success: (res) => {
        if (res.confirm) {
          const token = wx.getStorageSync('token');
          const openid = wx.getStorageSync('openid');
          const profile = wx.getStorageSync('userProfile');

          wx.clearStorageSync();

          if (token) wx.setStorageSync('token', token);
          if (openid) wx.setStorageSync('openid', openid);
          if (profile) wx.setStorageSync('userProfile', profile);

          this.calcCache();
          wx.showToast({ title: '已清除', icon: 'success' });
        }
      },
    });
  },

  // ─── About ───
  onAbout() {
    wx.showModal({
      title: '关于',
      content: '校园墙查询 v1.0.0\n\n一款校园信息查询与AI问答小工具，仅供校内同学使用。',
      showCancel: false,
      confirmText: '知道了',
    });
  },
});
