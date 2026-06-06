const { request } = require('../../utils/request');
const { withTheme } = require('../../utils/theme');

Page(withTheme({
  data: {
    keyword: '',
    results: [],
    total: 0,
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false,
    searched: false,
    hotPosts: [],
    hotLoading: false,
  },

  _debounceTimer: null,

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
    if (!this.data.searched) {
      this.loadHotPosts();
    }
  },

  loadHotPosts() {
    if (this.data.hotLoading) return;
    this.setData({ hotLoading: true });
    request({ url: '/posts/popular', data: { limit: 10 } })
      .then((res) => {
        this.setData({
          hotPosts: res.items || [],
          hotLoading: false,
        });
      })
      .catch(() => {
        this.setData({ hotLoading: false });
      });
  },

  onHotItemTap(e) {
    const id = e.currentTarget.dataset.id;
    if (!id) return;
    request({ url: `/posts/${id}/view`, method: 'POST', data: {} }).catch(() => {});
    setTimeout(() => this.loadHotPosts(), 500);
  },

  onShareAppMessage() {
    const kw = this.data.keyword.trim();
    return {
      title: kw ? `校园墙搜索：${kw}` : '校园墙查询 - 快速找到你想看的贴文',
      path: '/pages/search/search',
    };
  },

  onShareTimeline() {
    return {
      title: '校园墙查询 - 校园贴文一键搜索',
      query: '',
    };
  },

  onInput(e) {
    const val = e.detail.value;
    this.setData({ keyword: val });

    if (this._debounceTimer) clearTimeout(this._debounceTimer);
    if (!val.trim()) {
      this.setData({ searched: false, results: [], total: 0 });
      return;
    }

    this._debounceTimer = setTimeout(() => {
      this.doSearch(true);
    }, 500);
  },

  onSearch() {
    if (!this.data.keyword.trim()) return;
    this.doSearch(true);
  },

  onClear() {
    this.setData({
      keyword: '',
      results: [],
      total: 0,
      searched: false,
      noMore: false,
      page: 1,
    });
  },

  onReachBottom() {
    if (this.data.noMore || this.data.loading || !this.data.searched) return;
    this.doSearch(false);
  },

  doSearch(reset) {
    if (this.data.loading) return;

    const page = reset ? 1 : this.data.page;
    this.setData({ loading: true });

    if (reset) {
      const count = (wx.getStorageSync('stat_search') || 0) + 1;
      wx.setStorageSync('stat_search', count);
    }

    request({
      url: '/posts/search',
      data: {
        q: this.data.keyword.trim(),
        page,
        page_size: this.data.pageSize,
      },
    })
      .then((res) => {
        const items = res.items || [];
        const allResults = reset ? items : this.data.results.concat(items);
        const noMore = allResults.length >= res.total;

        this.setData({
          results: allResults,
          total: res.total,
          page: page + 1,
          loading: false,
          noMore,
          searched: true,
        });
      })
      .catch(() => {
        this.setData({ loading: false, searched: true });
      });
  },
}));
