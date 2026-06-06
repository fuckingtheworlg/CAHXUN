/**
 * 主题管理 — 3 套风格切换
 * - vibrant: Vibrant Campus（紫色梦境）
 * - ethos:   Ethos Premium（极简学术）
 * - azure:   Azure Vitality（海蓝活力）
 */

const STORAGE_KEY = 'app_theme';
const DEFAULT_THEME = 'vibrant';

const THEMES = [
  {
    key: 'vibrant',
    name: '紫色梦境',
    sub: 'Vibrant Campus',
    desc: '活力派对、彩色渐变、超圆角',
    primary: '#6b38d4',
    accent: '#3fe1fd',
    gradient: ['#6b38d4', '#8455ef', '#fbc2eb'],
  },
  {
    key: 'ethos',
    name: '清新薄荷',
    sub: 'Ethos Mint',
    desc: '柔和薄荷绿，清爽自然',
    primary: '#3a9b85',
    accent: '#a8e6cf',
    gradient: ['#5cb89e', '#7dc8b0', '#a8e6cf'],
  },
  {
    key: 'azure',
    name: '海蓝活力',
    sub: 'Azure Vitality',
    desc: '科技蓝 + 薄荷绿、清爽明快',
    primary: '#00a3ff',
    accent: '#00dfc1',
    gradient: ['#00629d', '#00a3ff', '#00dfc1'],
  },
];

function getCurrent() {
  try {
    return wx.getStorageSync(STORAGE_KEY) || DEFAULT_THEME;
  } catch (e) {
    return DEFAULT_THEME;
  }
}

function setCurrent(key) {
  if (!THEMES.find((t) => t.key === key)) return;
  try {
    wx.setStorageSync(STORAGE_KEY, key);
  } catch (e) {}
  const app = getApp();
  if (app) {
    app.globalData = app.globalData || {};
    app.globalData.theme = key;
  }
}

function getThemes() {
  return THEMES;
}

function getThemeInfo(key) {
  return THEMES.find((t) => t.key === (key || getCurrent())) || THEMES[0];
}

/**
 * 给页面添加 mixin：自动在 onShow 时同步主题。
 * 用法：Page(withTheme({ data: {...}, onShow() {...} }))
 */
function withTheme(pageObj) {
  const originalData = pageObj.data || {};
  const originalOnShow = pageObj.onShow;
  const originalOnLoad = pageObj.onLoad;

  pageObj.data = { theme: getCurrent(), ...originalData };

  pageObj.onLoad = function (...args) {
    this.setData({ theme: getCurrent() });
    if (typeof originalOnLoad === 'function') originalOnLoad.apply(this, args);
  };

  pageObj.onShow = function (...args) {
    const cur = getCurrent();
    if (this.data.theme !== cur) this.setData({ theme: cur });
    if (typeof originalOnShow === 'function') originalOnShow.apply(this, args);
  };

  return pageObj;
}

module.exports = {
  getCurrent,
  setCurrent,
  getThemes,
  getThemeInfo,
  withTheme,
  DEFAULT_THEME,
};
