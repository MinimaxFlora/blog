---
title: 这个博客是怎么搭起来的
date: 2026-10-24 13:00:00
updated: 2026-10-24 13:00:00
tags:
  - Hexo
  - GitHub Pages
  - Cloudflare
  - 备忘
categories:
  - 技术
keywords: Hexo, anzhiyu, GitHub Pages, Cloudflare, 建站
description: 记录整套建站与发布流程，方便以后复制或排查问题。
cover: /img/cover/2.jpg
top_group_list: 5
top_img: false
---

把这套东西记下来，省得以后重装或者换机器时又要从头查一遍。

## 技术栈

| 环节 | 用的什么 |
| --- | --- |
| 生成器 | Hexo 8 |
| 主题 | [anzhiyu](https://github.com/anzhiyu-c/hexo-theme-anzhiyu)（安知鱼） |
| 构建 | GitHub Actions |
| 托管 | GitHub Pages |
| 域名 | Cloudflare DNS，证书由 Pages 自动签发 |

## 目录约定

```
_config.yml            # 站点配置：标题、URL、搜索、订阅、站点地图
_config.anzhiyu.yml    # 主题配置：菜单、横幅、首页卡片、侧边栏
themes/anzhiyu/        # 主题本体，git submodule，不要直接改
source/                # 文章和页面
```

主题用 submodule 管理，好处是版本锁定、仓库干净；代价是**克隆时必须带 `--recursive`**，否则 `themes/anzhiyu` 是空目录，构建直接失败。

```bash
git clone --recursive https://github.com/MinimaxFlora/blog.git
# 已经克隆过、但主题目录是空的：
git submodule update --init --recursive
```

## 发布流程

推送到 `main` 就会触发 `.github/workflows/deploy.yml`：

1. 检出代码，含 submodule
2. `npm ci` 装依赖
3. `npx hexo generate` 生成静态文件到 `public/`
4. 上传 artifact，交给 `actions/deploy-pages` 发布

整个过程一分半左右，不需要在本地构建后再推 `gh-pages` 分支。

## 域名是怎么绑上的

三步：

1. `source/CNAME` 里写 `blog.tatalvpai.vip`，构建时会带到产物根目录
2. Cloudflare 加一条 CNAME：`blog` → `minimaxflora.github.io`
3. 仓库 Settings → Pages 里填自定义域名，等证书签发，然后勾上 Enforce HTTPS

DNS 记录**先不要开橙色云朵**。开着代理时 GitHub 验证域名容易失败，证书签不出来；等证书下来了再考虑开代理，并且要把 SSL/TLS 模式设成 **Full (strict)**，否则会重定向循环。

## 踩到的几个坑

**1. 首屏大图的配置不是 URL**

`index_img` 填的是一整条 CSS 声明，不是图片地址：

```yaml
index_img: "background: url(/img/banner.jpg) top / cover no-repeat"
```

**2. 新版 Chrome 里 `display: -webkit-box` 不生效了**

主题用 `-webkit-line-clamp` 做多行截断，但把 `display: -webkit-box` 解析成了 `flow-root`，结果盒子高度直接塌成 0，摘要整段消失。改用 `display: block` + `max-height` 截断才正常。

**3. 主题自带的演示内容要清掉**

默认配置里有主题作者自己的收款码、网易云歌单、示例分类和推广横幅。不清掉的话，打赏弹窗里出现的就是别人的二维码。

**4. 副标题的打字效果**

`subtitle.source` 默认开启了第三方一言接口，国内访问不稳定，关掉用自定义文案更可靠。

## 日常怎么写文章

```bash
npx hexo new "文章标题"   # 在 source/_posts/ 下生成
npm run server            # 本地预览 localhost:4000
git add -A && git commit -m "post: 文章标题" && git push
```

推上去就自动发布了，剩下的不用管。
