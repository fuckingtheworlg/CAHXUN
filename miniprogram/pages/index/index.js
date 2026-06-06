const { request } = require('../../utils/request');
const { withTheme } = require('../../utils/theme');

Page(withTheme({
  data: {
    posts: [],
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false,
    totalPosts: 0,
    greeting: '欢迎回来，校园动态尽在掌握',
    greetingTag: 'Hi',
    fabHidden: false,
  },

  onCreatePost() {
    wx.navigateTo({ url: '/pages/post-create/post-create' });
  },

  onShow() {
    const app = getApp();
    if (app && app.globalData && app.globalData.needRefreshIndex) {
      app.globalData.needRefreshIndex = false;
      this.setData({ page: 1, noMore: false, posts: [] });
      this.loadPosts();
    }
  },

  onPageScroll() {
    if (!this.data.fabHidden) {
      this.setData({ fabHidden: true });
    }
    if (this._fabTimer) clearTimeout(this._fabTimer);
    this._fabTimer = setTimeout(() => {
      this.setData({ fabHidden: false });
    }, 600);
  },

  onLoad() {
    this.updateGreeting();
    this.loadPosts();
  },

  updateGreeting() {
    const h = new Date().getHours();
    let g = '欢迎回来，校园动态尽在掌握';
    let tag = 'Hi';
    if (h < 6) { g = '夜深了，注意休息'; tag = '夜'; }
    else if (h < 12) { g = '早上好，新的一天开始啦'; tag = '早'; }
    else if (h < 14) { g = '中午好，吃了么'; tag = '午'; }
    else if (h < 18) { g = '下午好，校园新鲜事'; tag = '下'; }
    else { g = '晚上好，看看今天发生了什么'; tag = '晚'; }
    this.setData({ greeting: g, greetingTag: tag });
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false, posts: [] });
    this.loadPosts().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.noMore || this.data.loading) return;
    this.loadPosts();
  },

  onShareAppMessage() {
    return {
      title: '校园墙查询 - 校园动态一网打尽',
      path: '/pages/index/index',
      imageUrl: '',
    };
  },

  onShareTimeline() {
    return {
      title: '校园墙查询 - 校园动态一网打尽',
      query: '',
    };
  },

  loadPosts() {
    if (this.data.loading) return Promise.resolve();
    this.setData({ loading: true });

    return request({
      url: '/posts',
      data: {
        page: this.data.page,
        page_size: this.data.pageSize,
      },
    })
      .then((res) => {
        const newPosts = res.items || [];
        const allPosts = this.data.page === 1 ? newPosts : this.data.posts.concat(newPosts);
        const noMore = allPosts.length >= res.total;

        this.setData({
          posts: allPosts,
          page: this.data.page + 1,
          loading: false,
          noMore,
          totalPosts: res.total || 0,
        });
      })
      .catch(() => {
        this.setData({ loading: false });
      });
  },
}));
