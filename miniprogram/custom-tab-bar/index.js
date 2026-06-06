const { getCurrent } = require('../utils/theme');

Component({
  data: {
    selected: 0,
    color: '#999999',
    theme: 'vibrant',
    list: [
      {
        pagePath: '/pages/index/index',
        text: '首页',
        iconPath: '/assets/tab-home.png',
      },
      {
        pagePath: '/pages/search/search',
        text: '搜索',
        iconPath: '/assets/tab-search.png',
      },
      {
        pagePath: '/pages/chat/chat',
        text: 'AI问答',
        iconPath: '/assets/tab-chat.png',
      },
      {
        pagePath: '/pages/profile/profile',
        text: '我的',
        iconPath: '/assets/tab-profile.png',
      },
    ],
  },

  lifetimes: {
    attached() {
      this.setData({ theme: getCurrent() });
    },
  },

  pageLifetimes: {
    show() {
      const cur = getCurrent();
      if (this.data.theme !== cur) this.setData({ theme: cur });
    },
  },

  methods: {
    switchTab(e) {
      const { path, index } = e.currentTarget.dataset;
      wx.switchTab({ url: path });
      this.setData({ selected: index });
    },
  },
});
