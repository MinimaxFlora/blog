---
title: Debian 13 搭建 Xboard 面板：Docker Compose + Caddy HTTPS
date: 2026-10-26 21:10:00
updated: 2026-10-26 21:10:00
tags:
  - Xboard
  - Debian
  - Docker
  - Linux
  - 建站教程
categories:
  - 技术
keywords: Xboard, Xboard搭建, Debian 13, Docker Compose, Caddy, HTTPS, 节点部署, 机场面板
description: 从零开始在 Debian 13 上使用 Docker Compose 部署 Xboard，并通过 Caddy 配置 HTTPS，包含域名解析、基础安全、节点接入、更新和常见故障排查。
cover: /img/cover/xboard-deployment.jpg
top_img: /img/cover/xboard-banner.jpg
---

# Debian 13 搭建 Xboard 面板：Docker Compose + Caddy HTTPS

本文记录从零搭建 Xboard 面板的完整流程，使用 **Debian 13 + Docker Compose + Caddy**。内容包含服务器准备、域名解析、Xboard 初始化、HTTPS 反向代理、后台基础设置、节点接入、更新备份和常见问题排查。

本文优先采用 Xboard 官方提供的 Compose 部署模板，不需要在宿主机单独安装 PHP、MySQL 或 Redis。入门部署使用 SQLite 和模板提供的 Redis 配置，适合个人测试和轻量使用；如果用户量较大或需要更复杂的数据库架构，应根据官方文档调整部署方式。

> ⚠️ 请在遵守所在地法律法规、服务器厂商服务条款及网络使用政策的前提下部署和使用。生产环境上线前，请务必完成安全配置和备份。

---

## 🖼️ Xboard 前台界面预览

部署完成后，用户可以通过浏览器访问面板，登录后查看套餐信息、剩余流量、账户余额以及客户端使用说明。以下图片展示的是“探索无限”的界面效果；实际界面可能因 Xboard 版本、主题和站点配置而有所不同。

### 1️⃣ 前台欢迎页

![探索无限 Xboard 前台欢迎页](/img/xboard/xboard-welcome.png)

### 2️⃣ 用户仪表盘

![探索无限 Xboard 用户仪表盘](/img/xboard/xboard-dashboard.png)

> 图片文件请放在博客仓库的 `source/img/xboard/` 目录下，分别命名为 `xboard-welcome.png` 和 `xboard-dashboard.png`，再提交到 GitHub Pages 仓库。

---

## 🧰 一、事前准备

### 1️⃣ 准备服务器

建议准备一台干净的 Debian 13 服务器作为面板服务器：

| 项目 | 建议配置 |
| --- | --- |
| 操作系统 | Debian 13（trixie） |
| CPU | 2 vCPU 起步 |
| 内存 | 2 GB 起步，实际按使用量调整 |
| 硬盘 | 20 GB 以上 SSD |
| 公网端口 | `80/tcp`、`443/tcp` |
| 部署方式 | Docker Compose |

节点服务器可以与面板服务器分开部署。面板服务器负责网站、用户和订阅管理；节点服务器负责实际的网络服务。二者是否需要分离，应根据使用场景和资源情况决定。

### 2️⃣ 准备域名

建议先准备一个用于访问面板的域名，例如：

```text
面板域名：panel.example.com
节点域名：node1.example.com（可选）
```

请将 `example.com` 替换成自己的域名，下面出现的示例地址也需要同步替换。

在 DNS 服务商处添加 A 记录：

| 类型 | 主机记录 | 记录值 | 说明 |
| --- | --- | --- | --- |
| A | `panel` | 面板服务器公网 IP | 访问 Xboard 面板 |
| A | `node1` | 节点服务器公网 IP | 可选，供节点连接使用 |

如果使用 Cloudflare，初次部署建议先将面板记录设置为 **仅 DNS（灰云）**，确保域名直接解析到服务器，先完成 Caddy 证书申请和 HTTPS 测试。节点如果使用 Hysteria2 等 UDP 协议，也应使用仅 DNS，普通 Cloudflare 网站代理不能直接代理任意 UDP 节点流量。

检查解析是否正确：

```bash
# 把域名替换成你自己的面板域名
getent ahosts panel.example.com
```

输出的 IP 应与面板服务器公网 IP 一致。如果仍然解析到旧 IP，请先检查 DNS 记录并等待解析缓存更新。

### 3️⃣ 登录服务器并更新系统

以下命令默认使用 `root` 用户执行；如果使用普通用户，请在命令前加 `sudo`。

```bash
apt update
apt full-upgrade -y
apt install -y curl ca-certificates git gnupg nano
```

查看系统版本：

```bash
cat /etc/os-release
```

确认系统为 Debian 13 后再继续。其他发行版的包管理命令可能不同。

### 4️⃣ 配置基础防火墙（可选）

如果准备使用 UFW 管理防火墙，可以执行：

```bash
apt install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status verbose
```

⚠️ 如果 SSH 使用的不是默认 22 端口，必须先放行你实际使用的 SSH 端口，再启用防火墙，否则可能把自己锁在服务器外。云厂商控制台中的安全组也需要开放 TCP 80 和 443。

---

## 🐳 二、安装 Docker

Xboard 官方提供 Docker Compose 部署方式，推荐新手采用这种方式，避免在宿主机上手动处理 PHP、扩展和运行环境。

### 1️⃣ 安装 Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

确认 Docker 和 Compose 插件安装成功：

```bash
docker --version
docker compose version
systemctl status docker --no-pager
```

如果 `docker compose version` 没有输出版本号，说明 Compose 插件可能没有正确安装，需要先修复 Docker 安装，再继续部署。

---

## 📦 三、下载并初始化 Xboard

### 1️⃣ 下载官方 Compose 分支

进入 `/opt` 目录并下载 Xboard：

```bash
mkdir -p /opt
cd /opt
git clone -b compose --depth 1 https://github.com/cedar2025/Xboard.git
cd /opt/Xboard
```

官方仓库地址：<https://github.com/cedar2025/Xboard>

将官方提供的示例 Compose 配置复制为实际使用的配置文件：

```bash
cp compose.sample.yaml compose.yaml
```

> `compose.yaml` 是本机部署配置。不要跳过复制这一步；后续修改端口、环境变量等内容时，编辑本机的 `compose.yaml`，不要直接修改示例文件。

### 2️⃣ 将面板端口限制为本机访问

为了避免用户绕过 HTTPS 直接通过 `http://服务器IP:7001` 访问面板，建议只允许服务器本机访问 7001，再交给 Caddy 反向代理。

编辑配置文件：

```bash
nano compose.yaml
```

在 `xboard` 服务中找到 `ports`，如果看到：

```yaml
ports:
  - "7001:7001"
```

将其改成：

```yaml
ports:
  - "127.0.0.1:7001:7001"
```

如果你的模板中没有 `ports` 配置，请先对照当前模板的服务结构再修改，不要把这段随意粘贴到错误的缩进层级。保存后退出编辑器。

### 3️⃣ 初始化安装

将命令中的邮箱换成你准备使用的管理员邮箱：

```bash
docker compose run -it --rm \
  -e ENABLE_SQLITE=true \
  -e ENABLE_REDIS=true \
  -e ADMIN_ACCOUNT="admin@example.com" \
  xboard php artisan xboard:install
```

其中：

- `ENABLE_SQLITE=true`：启用 SQLite，入门部署不需要单独准备 MySQL。
- `ENABLE_REDIS=true`：启用模板支持的 Redis 配置。
- `ADMIN_ACCOUNT`：填写管理员账号使用的邮箱，请替换示例地址。

安装过程中请留意终端输出。安装成功后会给出管理员登录信息或后台地址等内容，**请立即保存好管理员账号、密码和后台路径**，不要把密码提交到公开仓库或截图发给他人。

### 4️⃣ 启动 Xboard

```bash
docker compose up -d
docker compose ps
```

查看日志：

```bash
docker compose logs --tail=100 xboard
```

检查本机端口是否可访问：

```bash
curl -I http://127.0.0.1:7001
```

返回 `200`、`302` 等正常 HTTP 响应通常说明 Web 服务已经有响应。如果连接失败，请先查看容器状态和日志，不要急着配置反向代理。

确认端口只监听本机地址：

```bash
ss -lntp | grep 7001
```

预期可以看到 `127.0.0.1:7001`，而不是 `0.0.0.0:7001`。这可以降低外部绕过 HTTPS 访问面板的风险。

---

## 🔐 四、安装 Caddy 并配置 HTTPS

Caddy 可以根据域名自动申请和续期 HTTPS 证书，适合用于 Xboard 的反向代理。这里使用 Caddy 官方 APT 软件源。

### 1️⃣ 安装 Caddy

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl gnupg

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | tee /etc/apt/sources.list.d/caddy-stable.list

chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
chmod o+r /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy
```

官方安装说明：<https://caddyserver.com/docs/install>

### 2️⃣ 编写 Caddyfile

先备份配置文件，再编辑：

```bash
cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
nano /etc/caddy/Caddyfile
```

将内容替换为下面的配置，并把 `panel.example.com` 改成自己的域名：

```caddyfile
panel.example.com {
    encode zstd gzip
    reverse_proxy 127.0.0.1:7001
}
```

保存后检查并加载配置：

```bash
caddy fmt --overwrite /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile
systemctl enable --now caddy
systemctl reload caddy
systemctl status caddy --no-pager
```

如果验证配置时报错，先根据报错修复语法，不要在配置未通过检查时反复重启服务。

### 3️⃣ 测试 HTTPS

```bash
curl -I https://panel.example.com
```

浏览器打开 `https://panel.example.com`，确认页面可以访问且浏览器没有证书错误。

**Caddy 无法申请证书时，优先检查以下事项：**

1. `panel.example.com` 是否解析到了这台服务器的公网 IP。
2. 云安全组和服务器防火墙是否放行了 TCP 80、443。
3. 是否有其他 Web 服务占用了 80 或 443。
4. 如果使用 Cloudflare，初次排查时可先切换为仅 DNS，确认源站证书申请成功后再考虑开启代理。

> 注意：Cloudflare 的 SSL/TLS 加密模式不要设置为“灵活（Flexible）”。如果之后开启 Cloudflare 代理，建议使用“完全（严格）/ Full (strict)”，并确认源站 Caddy 的 HTTPS 证书有效。

---

## ⚙️ 五、首次登录与后台基础配置

访问：

```text
https://panel.example.com
```

使用安装时生成或设置的管理员账号登录。不同 Xboard 版本的后台布局和字段名称可能存在差异，请以实际安装版本显示的设置项为准。

### 1️⃣ 站点设置

建议先检查以下内容：

| 设置项 | 建议填写 |
| --- | --- |
| 站点名称 | 自己的站点名称 |
| 站点 URL | `https://panel.example.com` |
| 订阅 URL | 初期可使用同一个 HTTPS 域名；如需分离域名，需另行配置 DNS 和反向代理 |
| 后台路径 | 如果版本支持，修改为不容易被猜到的路径 |
| 注册功能 | 确认是否真的需要开放注册 |

如果修改了后台路径，按当前版本提示重启对应服务，使配置生效。不要将管理入口、管理员密码或节点 Token 写进公开文章。

### 2️⃣ 配置邮件服务（按需）

如果要开放注册、邮箱验证或找回密码，需要配置可正常发信的 SMTP 服务。具体参数由邮件服务商提供，一般需要填写 SMTP 主机、端口、加密方式、用户名、密码和发件人地址。

注意：Cloudflare Email Routing 主要用于收件转发，不等于 SMTP 发信服务。配置完成后应实际测试注册验证邮件和密码重置邮件是否能够正常收到。

### 3️⃣ 上线前的安全检查

- 管理员使用强密码，不要重复使用其他网站的密码。
- 只开放实际需要的端口；面板的 7001 端口保持仅本机监听。
- 如果不需要公开注册，就关闭注册或按需限制注册方式。
- 确认邮件验证、验证码和订阅保护等功能是否符合你的使用场景。
- 定期备份数据库、环境配置、主题和插件文件。

---

## 🌐 六、添加节点服务器

面板能正常访问后，如果你需要接入独立节点服务器，可以按下面的流程进行。**面板本身不会自动提供可用节点线路**，节点还需要安装相应的节点端程序、配置协议和放通端口。

### 1️⃣ 准备节点服务器

节点服务器同样建议使用受支持的 Linux 发行版。先为节点域名添加 DNS 记录，例如 `node1.example.com` 指向节点服务器公网 IP。

如果使用 Cloudflare，提供节点服务的域名通常应设为仅 DNS。节点协议实际需要开放哪些 TCP/UDP 端口，应以节点后台配置和所选协议为准；如果使用 Hysteria2 等 UDP 协议，请确认云安全组和服务器防火墙都放行对应 UDP 端口。

### 2️⃣ 在 Xboard 后台创建节点

进入后台的节点管理页面，按照当前版本提供的选项新建节点：

1. 选择实际要使用的节点协议和类型。
2. 设置节点名称、地址、端口、流量倍率、权限组等参数。
3. 保存后记录节点 ID，并查看当前版本提供的节点端安装或接入说明。
4. 在对应节点服务器上安装与该 Xboard 版本兼容的节点端程序，并填入面板地址、Token 和节点 ID 等必要信息。

不同 Xboard 版本的节点后端、部署方式和配置字段可能不完全相同。建议优先使用你安装版本的后台生成命令或其官方说明，不要将旧教程里的节点脚本直接套用到新版面板。

如果你计划采用独立的 Xboard-Node 项目，请先确认它与当前面板版本兼容。该项目提供 Linux 安装脚本；建议先下载并检查脚本，再执行，而不是不看内容就直接通过管道运行远程脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/cedar2025/Xboard-Node/dev/install.sh -o /tmp/xboard-node-install.sh
less /tmp/xboard-node-install.sh
```

确认来源和内容无误，并核对当前面板版本的接入要求后，再将示例中的域名、Token 和节点 ID 替换成实际值：

```bash
bash /tmp/xboard-node-install.sh \
  --mode node \
  --panel "https://panel.example.com" \
  --token "替换为后台提供的Token" \
  --node-id 1
```

安装后可以根据该项目文档使用 `xbctl status`、`xbctl list` 查看状态。项目地址：<https://github.com/cedar2025/Xboard-Node>。不要把 Token 暴露到公开仓库、博客或聊天截图中。**如果当前 Xboard 版本提供了专属的节点安装命令，请以当前版本的官方说明为准，不要混用不同节点后端的安装方式。**

### 3️⃣ 验证节点在线

安装完成后回到 Xboard 后台查看节点状态，并从实际客户端进行连接测试。节点离线时，优先检查：

- 面板域名是否能从节点服务器正常访问，HTTPS 证书是否有效。
- 面板地址、节点 ID 和 Token 是否填写正确。
- 节点服务是否启动，日志是否有鉴权或连接错误。
- 云厂商安全组、系统防火墙、协议端口和 DNS 记录是否正确。

Caddy 这里配置的是面板的 HTTP/HTTPS 流量代理，不能直接当作任意 UDP 节点流量的通用代理。

---

## 🔄 七、更新与备份

### 1️⃣ 更新 Xboard

更新前务必备份数据，并阅读当前版本的升级说明。官方 Compose 部署通常可以在项目目录中拉取新镜像并重建服务：

```bash
cd /opt/Xboard
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail=100 xboard
```

当前官方 Compose 模板可能会在容器启动时执行版本更新任务；如果你使用的是较早的 Compose 模板，请先核对官方升级文档，不要假设所有旧模板行为完全相同。

### 2️⃣ 备份重要文件

SQLite 数据、环境配置、主题、插件和 Compose 配置都很重要。可先建立备份目录：

```bash
mkdir -p /opt/backups
```

建议在维护窗口内短暂停止服务，复制数据文件后再启动服务，以降低备份期间数据库写入造成不一致的风险：

```bash
cd /opt/Xboard
docker compose stop

BACKUP_FILE="/opt/backups/xboard-$(date +%F-%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" \
  .env .docker/.data storage/theme plugins compose.yaml

docker compose start
ls -lh "$BACKUP_FILE"
```

如果你的部署没有其中某个目录或文件，先检查当前目录结构，再按实际存在的路径调整备份命令。备份文件包含敏感配置，应存放在权限受控的位置，并定期复制到另一台安全的存储设备。**备份文件不是备份方案的全部，建议定期演练恢复流程。**

---

## 🛠️ 八、常见问题排查

### ❌ 1. 浏览器访问面板显示 502 Bad Gateway

先检查 Xboard 容器：

```bash
cd /opt/Xboard
docker compose ps
docker compose logs --tail=200 xboard
curl -I http://127.0.0.1:7001
```

如果本机 `curl` 都无法连接，先解决容器启动问题。如果本机正常但域名返回 502，再检查 Caddyfile 中的上游是否为 `127.0.0.1:7001`，以及 Caddy 是否运行正常：

```bash
caddy validate --config /etc/caddy/Caddyfile
journalctl -u caddy -n 100 --no-pager
```

### ❌ 2. HTTPS 证书申请失败

检查域名解析、TCP 80/443、安全组和服务器防火墙。如果面板域名仍指向旧服务器，或者端口被其他 Web 服务占用，Caddy 就可能无法完成验证。

查看日志：

```bash
journalctl -u caddy -n 200 --no-pager
```

### ❌ 3. Docker 容器启动失败或拉取镜像失败

```bash
cd /opt/Xboard
docker compose ps
docker compose logs --tail=200 xboard
docker compose pull
```

检查服务器到 GitHub Container Registry（GHCR）的网络连通性、磁盘空间以及 Compose 文件是否正确。不要在没有核实来源的情况下随意改用第三方镜像或不明安装脚本。

### ❌ 4. 7001 端口从外部无法访问

如果你按照本文将端口绑定为 `127.0.0.1:7001:7001`，外部无法直接访问 7001 是**预期的安全行为**。请通过 `https://panel.example.com` 访问面板。如果本机 Caddy 也无法连接，再检查 Xboard 是否运行以及本机 7001 端口是否监听。

### ❌ 5. 节点一直离线

检查节点端程序状态和日志、面板地址、Token、节点 ID、DNS 解析和协议端口。若所选协议使用 UDP，必须同时检查云安全组和系统防火墙中的 UDP 规则；仅开放 TCP 端口通常不够。

---

## ✅ 九、部署完成后的检查清单

- [ ] 面板域名解析到正确的服务器公网 IP。
- [ ] Docker 和 Xboard 容器运行正常。
- [ ] 本机访问 `http://127.0.0.1:7001` 有正常 HTTP 响应。
- [ ] `7001` 仅绑定在 `127.0.0.1`，没有直接暴露到公网。
- [ ] Caddy 配置验证通过，HTTPS 证书正常。
- [ ] 已保存管理员登录信息并使用强密码。
- [ ] 已按需配置站点 URL、订阅 URL、邮件和注册策略。
- [ ] 节点端程序、节点域名和对应协议端口均已验证。
- [ ] 已建立备份，并确认备份文件可以读取。

至此，Xboard 面板的基础部署就完成了。后续的节点协议、用户套餐、流量策略和邮件配置，应根据你实际安装的 Xboard 版本及节点端兼容情况逐项设置，不要直接照搬与当前版本不匹配的旧配置。

---

## 📚 参考资料

- [Xboard 官方 GitHub 仓库](https://github.com/cedar2025/Xboard)
- [Linux 部署 Xboard 参考文章](https://blog.shishishi3.com/blog/xboard-linux-deployment-guide/)
- [Xboard Docker Compose 部署文档](https://github.com/cedar2025/Xboard/blob/master/docs/en/installation/docker-compose.md)
- [Xboard-Node 项目说明](https://github.com/cedar2025/Xboard-Node)
- [Caddy 官方安装文档](https://caddyserver.com/docs/install)
- [Caddy 反向代理快速入门](https://caddyserver.com/docs/quick-starts/reverse-proxy)
