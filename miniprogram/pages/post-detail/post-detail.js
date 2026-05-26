const { request } = require('../../utils/request');
const { ensureLogin } = require('../../utils/auth');

// 假评论数据（微信小程序 UGC 评论功能需要类目报备，先用静态数据占位）
const MOCK_COMMENTS = [
  {
    id: 1,
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=zhao',
    nickname: '小赵',
    content: '这个挺有用的，感谢分享！',
    time: '2 小时前',
    likes: 3,
  },
  {
    id: 2,
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=qian',
    nickname: '小钱',
    content: '我也遇到过类似情况，确实是这样～',
    time: '5 小时前',
    likes: 1,
  },
  {
    id: 3,
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=sun',
    nickname: '小孙',
    content: '收藏了 +1',
    time: '昨天',
    likes: 0,
  },
];

Page({
  data: {
    post: null,
    loading: true,
    liking: false,
    comments: MOCK_COMMENTS,
    showCommentTip: false,
  },

  onLoad(options) {
    const id = parseInt(options.id);
    if (!id) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 800);
      return;
    }
    this.postId = id;
    this.loadDetail();
    this.recordView();
  },

  recordView() {
    request({ url: `/posts/${this.postId}/view`, method: 'POST', data: {} }).catch(() => {});
  },

  loadDetail() {
    this.setData({ loading: true });
    request({ url: `/posts/${this.postId}` })
      .then((res) => {
        this.setData({ post: res, loading: false });
      })
      .catch(() => {
        this.setData({ loading: false });
      });
  },

  onLikeTap() {
    if (this.data.liking || !this.data.post) return;
    const post = this.data.post;

    ensureLogin()
      .then(() => {
        this.setData({ liking: true });
        const method = post.liked ? 'DELETE' : 'POST';
        return request({
          url: `/posts/${this.postId}/like`,
          method,
          data: {},
        });
      })
      .then((res) => {
        this.setData({
          'post.liked': res.liked,
          'post.like_count': res.count,
          liking: false,
        });
        if (res.liked) {
          wx.vibrateShort && wx.vibrateShort({ type: 'light' });
        }
      })
      .catch(() => {
        this.setData({ liking: false });
      });
  },

  onPreviewImage(e) {
    const url = e.currentTarget.dataset.url;
    const urls = (this.data.post && this.data.post.images) || [url];
    wx.previewImage({ current: url, urls });
  },

  onCommentInputFocus() {
    this.setData({ showCommentTip: true });
    setTimeout(() => this.setData({ showCommentTip: false }), 2500);
  },

  onShareAppMessage() {
    const post = this.data.post;
    const title = post && post.content
      ? post.content.slice(0, 30) + (post.content.length > 30 ? '...' : '')
      : '校园墙贴文';
    return {
      title,
      path: `/pages/post-detail/post-detail?id=${this.postId}`,
    };
  },

  onShareTimeline() {
    const post = this.data.post;
    return {
      title: post && post.content ? post.content.slice(0, 30) : '校园墙贴文',
      query: `id=${this.postId}`,
    };
  },
});
