const { request } = require('../../utils/request');

Component({
  properties: {
    post: {
      type: Object,
      value: {},
    },
  },

  data: {
    catClass: '',
  },

  lifetimes: {
    attached() {
      this.computeCatClass();
    },
  },

  observers: {
    'post.category': function () {
      this.computeCatClass();
    },
  },

  methods: {
    computeCatClass() {
      const cat = (this.data.post && this.data.post.category) || '';
      if (!cat) {
        this.setData({ catClass: '' });
        return;
      }
      let hash = 0;
      for (let i = 0; i < cat.length; i++) hash += cat.charCodeAt(i);
      const variants = ['cat-a', 'cat-b', 'cat-c', 'cat-d'];
      this.setData({ catClass: variants[hash % variants.length] });
    },

    onCardTap() {
      const id = this.data.post && this.data.post.id;
      if (!id) return;
      request({
        url: `/posts/${id}/view`,
        method: 'POST',
        data: {},
      }).catch(() => {});
    },

    onPreviewImage(e) {
      const url = e.currentTarget.dataset.url;
      wx.previewImage({
        current: url,
        urls: this.data.post.images || [url],
      });
    },
  },
});
