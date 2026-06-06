const { streamRequest } = require('../../utils/request');
const { ensureLogin } = require('../../utils/auth');
const { withTheme } = require('../../utils/theme');

let _msgId = 0;
function nextId() {
  return 'msg-' + ++_msgId;
}

Page(withTheme({
  data: {
    messages: [],
    inputValue: '',
    sending: false,
    scrollToId: '',
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
  },

  onShareAppMessage() {
    return {
      title: '校园墙 AI 问答 - 让 AI 帮你查校园动态',
      path: '/pages/chat/chat',
    };
  },

  onShareTimeline() {
    return {
      title: '校园墙 AI 问答 - 让 AI 帮你查校园动态',
      query: '',
    };
  },

  onInputChange(e) {
    this.setData({ inputValue: e.detail.value });
  },

  onHintTap(e) {
    const text = e.currentTarget.dataset.text;
    this.setData({ inputValue: text });
    this.onSend();
  },

  onSend() {
    const question = this.data.inputValue.trim();
    if (!question || this.data.sending) return;

    ensureLogin()
      .then(() => {
        this._doSend(question);
      })
      .catch(() => {
        wx.showModal({
          title: '需要登录',
          content: '使用 AI 问答功能需要先登录，是否前往登录？',
          confirmText: '去登录',
          success(res) {
            if (res.confirm) {
              wx.switchTab({ url: '/pages/profile/profile' });
            }
          },
        });
      });
  },

  _doSend(question) {
    const count = (wx.getStorageSync('stat_chat') || 0) + 1;
    wx.setStorageSync('stat_chat', count);

    const userMsg = { id: nextId(), role: 'user', content: question, typing: false };
    const aiMsg = { id: nextId(), role: 'assistant', content: '', typing: true };
    const messages = [...this.data.messages, userMsg, aiMsg];
    const aiIndex = messages.length - 1;

    this.setData({
      messages,
      inputValue: '',
      sending: true,
      scrollToId: 'scroll-bottom',
    });

    streamRequest(
      { url: '/chat', data: { question } },
      (chunk) => {
        const key = `messages[${aiIndex}].content`;
        this.setData({
          [key]: this.data.messages[aiIndex].content + chunk,
          scrollToId: 'scroll-bottom',
        });
      },
      (err) => {
        const typingKey = `messages[${aiIndex}].typing`;
        if (err) {
          const contentKey = `messages[${aiIndex}].content`;
          const current = this.data.messages[aiIndex].content;
          this.setData({
            [contentKey]: current || '抱歉，回答出错了，请稍后重试',
            [typingKey]: false,
            sending: false,
          });
        } else {
          this.setData({
            [typingKey]: false,
            sending: false,
          });
        }
      }
    );
  },
}));
