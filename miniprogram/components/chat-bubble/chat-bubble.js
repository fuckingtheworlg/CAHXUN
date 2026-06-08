Component({
  properties: {
    role: {
      type: String,
      value: 'user',
    },
    content: {
      type: String,
      value: '',
    },
    typing: {
      type: Boolean,
      value: false,
    },
    sources: {
      type: Array,
      value: [],
    },
  },

  methods: {
    onSourceTap(e) {
      const id = e.currentTarget.dataset.id;
      this.triggerEvent('sourcetap', { id });
    },
  },
});
