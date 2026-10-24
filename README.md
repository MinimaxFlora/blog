# Tatalvpai Blog

个人博客，基于 [Hexo](https://hexo.io/) + [安知鱼主题](https://github.com/anzhiyu-c/hexo-theme-anzhiyu)，
通过 GitHub Actions 自动构建并发布到 GitHub Pages，域名 `https://blog.tatalvpai.vip`。

## 线上地址

| 用途 | 地址 |
| --- | --- |
| 自定义域名 | https://blog.tatalvpai.vip |
| GitHub Pages | https://minimaxflora.github.io/blog/ |
| 仓库 | https://github.com/MinimaxFlora/blog |

## 环境要求

- Node.js >= 20.19.0（Hexo 8 的要求，CI 使用 Node 22）
- Git

## 本地开发

首次拉取仓库时主题是 git 子模块，需要一并拉取：

```bash
git clone --recursive https://github.com/MinimaxFlora/blog.git
# 已经 clone 过、但 themes/anzhiyu 是空的：
git submodule update --init --recursive
```

安装依赖并启动本地预览（默认 http://localhost:4000）：

```bash
npm install
npm run server
```

其他常用命令：

```bash
npm run build    # 生成静态文件到 public/
npm run clean    # 清除缓存和 public/
npx hexo new "文章标题"          # 新建文章 -> source/_posts/
npx hexo new page "页面标题"     # 新建页面 -> source/<页面标题>/index.md
```

## 写文章

新建的文章位于 `source/_posts/`，头部 front-matter 支持安知鱼主题的全部字段（标签、分类、置顶、封面、目录等），
模板见 `scaffolds/post.md`。

`top: 1` 表示置顶，`cover:` 可指定封面图，`top_img: false` 表示不使用顶部大图。

## 部署

推送到 `main` 分支即自动触发 `.github/workflows/deploy.yml`：

1. 检出代码（含子模块）
2. `npm ci` 安装依赖
3. `npx hexo generate` 生成静态站点
4. 上传 artifact 并用 `actions/deploy-pages` 发布到 GitHub Pages

也可以在 Actions 页面手动触发（`workflow_dispatch`）。

## 域名与 DNS

- `source/CNAME` 固定写入 `blog.tatalvpai.vip`，构建时会带到产物根目录
- Cloudflare 上 `blog` 记录为 CNAME，指向 `minimaxflora.github.io`
- HTTPS 证书由 GitHub Pages 自动签发（Let's Encrypt）

> 若在 Cloudflare 上开启了代理（橙色云朵），请把 SSL/TLS 模式设为 **Full (strict)**，
> 否则会出现重定向循环或证书错误。

## 目录结构

```
├── _config.yml            # 站点配置（标题、URL、插件、搜索/订阅/站点地图）
├── _config.anzhiyu.yml    # 主题覆盖配置（菜单、社交、横幅、搜索等）
├── scaffolds/             # 新建文章/页面的模板
├── source/
│   ├── _posts/            # 文章
│   ├── about/             # 关于页
│   ├── tags/              # 标签页
│   ├── categories/        # 分类页
│   ├── img/               # 自托管图片（横幅、头像、favicon）
│   └── CNAME              # 自定义域名
├── themes/anzhiyu/        # 主题（git submodule，勿直接改，改根目录覆盖配置）
└── tools/gen-assets.py    # 生成横幅/头像/OG 图片的脚本
```

主题升级：

```bash
git submodule update --remote themes/anzhiyu
```

升级后如主题配置项有新增，记得同步 `_config.anzhiyu.yml`。
