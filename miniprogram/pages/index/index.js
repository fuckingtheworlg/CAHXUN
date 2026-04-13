const { request } = require('../../utils/request');

Page({
  data: {
    posts: [],
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false,
  },

  onLoad() {
    this.loadPosts();
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
        });
      })
      .catch(() => {
        this.setData({ loading: false });
      });
  },
});
