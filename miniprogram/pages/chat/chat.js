const { streamRequest } = require('../../utils/request');
const { ensureLogin } = require('../../utils/auth');

let _msgId = 0;
function nextId() {
  return 'msg-' + ++_msgId;
}

Page({
  data: {
    messages: [],
    inputValue: '',
    sending: false,
    scrollToId: '',
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
        wx.showToast({ title: '登录失败，请重试', icon: 'none' });
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
});
