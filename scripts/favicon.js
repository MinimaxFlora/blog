// 用站点自己的图标覆盖根目录 /favicon.ico
// 主题自带的 source/favicon.ico 会盖掉站点同名文件，所以这里用生成器接管，
// 保证浏览器/爬虫直接请求 /favicon.ico 时拿到的也是 TS Blog 的图标。
const fs = require('node:fs');
const path = require('node:path');

const ICON = path.join(hexo.base_dir, 'source', 'img', 'brand', 'favicon.ico');

hexo.extend.generator.register('brand-favicon', function () {
  if (!fs.existsSync(ICON)) {
    this.log.warn('favicon.ico not found at %s', ICON);
    return [];
  }
  return {
    path: 'favicon.ico',
    data: () => fs.createReadStream(ICON),
  };
});
