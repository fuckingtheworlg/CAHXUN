Component({
  properties: {
    post: {
      type: Object,
      value: {},
    },
  },

  methods: {
    onPreviewImage(e) {
      const url = e.currentTarget.dataset.url;
      wx.previewImage({
        current: url,
        urls: this.data.post.images || [url],
      });
    },
  },
});
