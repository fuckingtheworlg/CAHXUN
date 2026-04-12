const { request } = require('../../utils/request');

Page({
  data: {
    keyword: '',
    results: [],
    total: 0,
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false,
    searched: false,
  },

  _debounceTimer: null,

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
});
