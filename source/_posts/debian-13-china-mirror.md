---
title: Debian 13 修改软件源（国内镜像）
date: 2026-10-24 22:00:00
updated: 2026-10-24 22:40:00
tags:
  - Debian
  - Linux
  - 换源
categories:
  - 技术
keywords: Debian 13, trixie, 换源, 国内镜像, sources.list, deb822, apt
description: Debian 13 换国内镜像源的完整教程：确认版本、备份、写入新源、验证、排错。
cover: /img/cover/debian13-source.jpg
top_img: /img/cover/debian13-banner.jpg
---

# Debian 13 修改软件源（国内镜像）

本文介绍 Debian 13（trixie）更换国内镜像源的完整流程：确认系统版本、备份原配置、写入新源、验证是否生效，最后附上常见报错的排查方法。命令都可以直接复制执行。

Debian 官方源在境外，国内直连更新索引经常卡住；换成国内镜像后，同样的事情几秒钟就能完成。

---

## 🧰 一、事前准备

### 1️⃣ 确认系统是 Debian 13

```bash
lsb_release -cs
```

输出 `trixie` 就对了。命令不存在的话，直接看系统信息：

```bash
. /etc/os-release && echo "$PRETTY_NAME / $VERSION_CODENAME"
# Debian GNU/Linux 13 (trixie) / trixie
```

版本代号对照，**用错代号会直接 404**：

| 系统版本 | 代号 |
| --- | --- |
| Debian 13 | `trixie` |
| Debian 12 | `bookworm` |
| Debian 11 | `bullseye` |

> ⚠️ 网上大部分教程写的是 `bookworm`（Debian 12），照抄到 13 上会报 `404 Not Found`。下面的命令都已经按 `trixie` 写好，直接复制即可。

### 2️⃣ 确认源文件是哪种格式

Debian 现在有两种写法，**改错文件等于白改**：

```bash
ls -l /etc/apt/sources.list /etc/apt/sources.list.d/*.sources 2>/dev/null
```

| 出现的文件 | 格式 | 常见于 |
| --- | --- | --- |
| `/etc/apt/sources.list` | 传统一行式 | 物理机、虚拟机、大部分 VPS |
| `/etc/apt/sources.list.d/debian.sources` | DEB822 | Debian 12 起的容器镜像、部分云镜像 |

两个文件都存在时 apt 会都读取，容易互相干扰。建议只保留实际在用的那个，另一个备份走。

### 3️⃣ 备份原始源

按你的格式执行对应的一条：

```bash
# 传统一行式
cp /etc/apt/sources.list /etc/apt/sources.list.bak

# DEB822 格式
cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak
```

---

## 🖼️ 二、开始换源

### 1. 🧩 传统格式（sources.list）

**腾讯云（推荐）** —— 整段复制，粘贴执行：

```bash
cat > /etc/apt/sources.list << EOF
deb https://mirrors.cloud.tencent.com/debian/ trixie main contrib non-free non-free-firmware
deb https://mirrors.cloud.tencent.com/debian/ trixie-updates main contrib non-free non-free-firmware
deb https://mirrors.cloud.tencent.com/debian/ trixie-backports main contrib non-free non-free-firmware
deb https://mirrors.cloud.tencent.com/debian-security/ trixie-security main contrib non-free non-free-firmware
EOF
```

**清华源** —— 用这个就复制这段：

```bash
cat > /etc/apt/sources.list << EOF
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-backports main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security/ trixie-security main contrib non-free non-free-firmware
EOF
```

想换其他镜像，把命令里的域名整体替换成下表任意一个：

| 镜像 | 域名 | 备注 |
| --- | --- | --- |
| 中科大 | `mirrors.ustc.edu.cn` | 支持多架构 |
| 阿里云 | `mirrors.aliyun.com` | ECS 内网用 `mirrors.cloud.aliyuncs.com` |
| 华为云 | `mirrors.huaweicloud.com` | 云厂商镜像 |
| 上海交大 | `mirror.sjtu.edu.cn` | 高校镜像 |
| 南京大学 | `mirror.nju.edu.cn` | 高校镜像 |
| 北京外国语大学 | `mirrors.bfsu.edu.cn` | 高校镜像 |
| 网易 | `mirrors.163.com` | 速度较慢，仅作备用 |

也可以用 `sed` 一条命令替换，不用重写文件：

```bash
sed -i 's|mirrors.cloud.tencent.com|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list
```

### 2. ⚙️ DEB822 格式（debian.sources）

如果你的系统是这个格式，改的是另一个文件：

```bash
cat > /etc/apt/sources.list.d/debian.sources << EOF
Types: deb
URIs: https://mirrors.cloud.tencent.com/debian
Suites: trixie trixie-updates trixie-backports
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://mirrors.cloud.tencent.com/debian-security
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF
```

注意 `Suites` 和 `Components` 是**空格分隔**，不是一行一个。

### 3. ✅ 更新并验证

```bash
apt update
```

正常输出长这样，`Get:` 后面应该全是你的镜像域名：

```
Get:1 https://mirrors.cloud.tencent.com/debian trixie InRelease [140 kB]
Get:2 https://mirrors.cloud.tencent.com/debian trixie-updates InRelease [47.3 kB]
Get:3 https://mirrors.cloud.tencent.com/debian-security trixie-security InRelease [48.1 kB]
Get:4 https://mirrors.cloud.tencent.com/debian trixie/main amd64 Packages [9,681 kB]
Fetched 9,916 kB in 1s (9,412 kB/s)
Reading package lists... Done
```

再确认一下实际生效的源：

```bash
apt policy
```

输出的 `http(s)://` 就是 apt 真正在用的地址。如果还混着 `deb.debian.org`，说明 `/etc/apt/sources.list.d/` 下还留着别的 `.list` 文件没清理。

最后升级系统：

```bash
apt upgrade -y
```

---

## ⚠️ 三、几个必须注意的点

- **`non-free-firmware` 组件不能漏**：Debian 12 起固件单独拆到这个组件，漏了它网卡、显卡驱动就装不上——这是「换完源能上网、但没有 WiFi」的最常见原因。
- **安全源建议留官方**：上面配置里的 `trixie-security` 指向 `security.debian.org`。镜像站有同步延迟，安全更新越早拿到越好，这也是 [Debian 官方 FAQ](https://www.debian.org/security/faq.en.html#mirror) 的建议。纯内网出不去外网的话，换成镜像的 `/debian-security` 也行。
- **云服务器优先用同厂商内网源**：阿里云 ECS 用 `mirrors.cloud.aliyuncs.com`，腾讯云 CVM 用 `mirrors.tencentyun.com`，走内网链路，通常能跑满带宽。
- **不要多源混用**：同一套源配多个镜像，apt 会同时向多个地址请求索引，反而更慢，还容易出现签名校验混乱。选一个最快的用就行。
- **`trixie-backports` 是可选的**：不追新内核、新驱动可以删掉这一行，少一行少一份维护负担。

---

## 🛠️ 四、常见问题

### ❌ 404 Not Found，找不到 dists/xxx/Release

套件名写错了。检查 `dists/` 后面那段是不是 `trixie`，以及域名有没有拼错（`aliyun` 写成 `aliyn` 这种）。

### ❌ NO_PUBKEY 签名验证失败

```
The following signatures couldn't be verified because the public key is not available
```

密钥环缺失或损坏，重装一下：

```bash
ls -l /usr/share/keyrings/debian-archive-keyring.gpg   # 文件应该存在
apt install --reinstall debian-archive-keyring
```

### ❌ Release file is not valid yet / has expired

系统时间不对，apt 校验签名会失败：

```bash
timedatectl status
timedatectl set-ntp true
```

### ❌ 证书错误 Certificate verification failed

```bash
apt install --reinstall ca-certificates
update-ca-certificates
```

系统太老拉不动 HTTPS 源的话，先临时把源改成 `http://`，装好证书再换回 `https://`。

### ❌ 下载大包时 Connection reset by peer

apt 2.1.9 之后的 HTTP Pipelining 和部分 Nginx 镜像有兼容问题，升级系统时容易触发。关掉即可：

```bash
echo 'Acquire::http::Pipeline-Depth "0";' > /etc/apt/apt.conf.d/99nopipelining
```

### ↩️ 恢复默认源

```bash
# 传统格式
cp /etc/apt/sources.list.bak /etc/apt/sources.list

# DEB822 格式
cp /etc/apt/sources.list.d/debian.sources.bak /etc/apt/sources.list.d/debian.sources

apt update
```

---

## 📌 小结

1. `lsb_release -cs` 确认代号是 `trixie`
2. `ls` 确认改的是 `sources.list` 还是 `debian.sources`
3. 备份 → 写入新源 → `apt update`
4. 出问题先看代号有没有写错、`non-free-firmware` 有没有漏

换完源，`apt` 才算真正好用了。
