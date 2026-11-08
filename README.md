# UnitDeck - 轻量级 Linux Systemd 服务 Web 管理工具

一个在浏览器中查看与控制 Linux 宿主机 systemd 服务的简单 Web 界面。

---

## 💡 开发背景与用途

在局域网内运行的 Linux 主机（如个人家庭服务器、AI 工作站或测试机）上，我们通常会把各种应用程序配置成 systemd 服务在后台长期运行（例如 ComfyUI、Ollama、自定义脚本或各类 Web 服务）。

但在日常使用中，频繁面临一些繁琐的小操作：
- 每次想启动、停止某个服务，或者看一眼服务有没有挂掉，都得打开 SSH 终端敲 `systemctl status/start/stop`；
- 想排查报错，又要在终端里打 `journalctl -u xxx -n 100`；
- 机器上跑了多个大程序时，资源快撑不住了，想把不用的服务关掉，得一个个敲命令停止；
- 用手机等移动设备临时想开关某个后台服务时，手机敲终端命令非常不便。

**UnitDeck 就是为了解决这些日常操作而做的一个简易面板**：
把你需要关心的后台服务集中放到一个网页上，点一下按钮就能启停、重启或查看最新日志，同时顺便看一眼当前 CPU、内存和显卡的实时占用情况。

---

## 🛠️ 主要功能

- **自主勾选纳管**：系统会自动列出机器上的 systemd 服务，您可以只勾选自己关心的几个常用程序显示在首页，并给它们起一个好辨认的中文别名。
- **服务状态与安全控制**：直观展示服务的当前运行状态（运行中、已停止、失败等），提供启动、停止、重启操作。带确认弹窗，避免在手机或平板上误触。
- **开机自启开关**：卡片右下角可直接切换该服务是否开机自启（`systemctl enable / disable`）。
- **一键全部停止**：当需要快速把机器资源腾出来跑其他任务时，可以一键停止所有正在运行的纳管服务。
- **在线查看实时日志**：点击卡片上的日志图标，可以在右侧抽屉里直接查看 `journalctl` 最新的运行日志，排查报错无需进 SSH。
- **基础硬件状态监测**：右上角提供一个紧凑的监控小弹窗，显示当前的 CPU 使用率及温度、系统内存（RAM）以及显卡（GPU/显存）的占用情况。
- **服务检索**：顶部带搜索框，可以通过按 `/` 键快速过滤筛选服务。

---

## 🛡️ 安全与防护机制

由于 UnitDeck 具有控制宿主机 systemd 与系统资源的特权，本软件内置了全方位的安全防护与操作护栏：

1. **工业级密码学与防爆破**：
   - 采用标准 **bcrypt** 密码哈希算法（自动加盐并在首次登录时无感迁移升级旧密码），废除弱哈希。
   - 内置基于客户端 IP 的**滑动窗口登录限流器**（1 分钟内连续输错 5 次密码将自动锁定 15 分钟），杜绝网络暴力破解。
2. **严格的会话与 Token 生命周期**：
   - 支持**真正的服务端登出注销**（`/api/auth/logout`），退出时立即销毁 Token。
   - 引入版本化控制（`token_version`），**修改密码时瞬间使所有已登录设备的旧会话全局失效**。
   - 校验逻辑全程使用常量时间比较函数（`secrets.compare_digest`），阻断计时侧信道攻击。
3. **系统核心基础设施保护护栏**：
   - 设立关键服务硬性黑名单：严禁对 `sshd`、`NetworkManager`、`docker` 等核心服务执行 `stop` 或 `disable` 操作，防止误触导致整台机器断网失联。
   - 对所有底层系统命令行调用注入参数分隔符 `--` 并严格限制服务名正则，杜绝参数注入。
4. **日志查阅范围收敛**：
   - 限制日志查看接口权限，只能读取用户已勾选纳管的服务日志，防止越权探测宿主机其他系统级敏感日志。
5. **显存清理防误杀机制**：
   - 触发一键释放显存（GPU Clean）时，内置宿主机**桌面图形会话与系统白名单**（保护 Xorg、Wayland、GNOME、KDE 及系统核心），杜绝无差别杀伤宿主机桌面与正常外部进程。
6. **规范 CORS 与接口文档收敛**：
   - 消除通配符与凭证冲突；生产环境下默认收敛 API 接口文档（`/docs`），杜绝元数据裸露。

---

## ⚙️ 它是怎么运行的？

UnitDeck 采用单个 Docker 容器部署，但它不是用来管理容器本身的，而是**管理外部宿主机系统的原生服务**：

1. **与宿主机 Systemd 交互**：容器通过只读或挂载宿主机的 `/run/systemd/system`、`/run/dbus/system_bus_socket` 以及 `systemctl` / `journalctl` 工具，直接与宿主机的 systemd 守护进程对话。宿主机无需额外安装任何后台 agent。
2. **硬件数据读取**：直接读取 Linux 内核的 `/proc/stat`、温度接口 `/sys/class/hwmon` 以及显卡节点，属于低开销的轻量轮询，不依赖其他外部监控套件。
3. **技术栈**：
   - 后端：Python 3.11 + FastAPI（提供轻量 REST API）
   - 前端：Vue 3 + TypeScript + TailwindCSS + DaisyUI（单页面应用）

---

## 🚀 部署方法

推荐使用 Docker Compose 部署。

### 1. 编写 `docker-compose.yml`

在服务器上创建工作目录（例如 `/opt/unitdeck`），新建 `docker-compose.yml`：

```yaml
services:
  unitdeck:
    image: crpi-tyyqcg8a2rpatesk.cn-shanghai.personal.cr.aliyuncs.com/zixidaxian/unitdeck:latest
    container_name: unitdeck
    restart: unless-stopped
    pid: host
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - DATA_DIR=/app/data
    volumes:
      # 保存已勾选的服务配置和密码文件
      - /opt/unitdeck/data:/app/data
      # 挂载宿主机 systemd 与 dbus 通道（控制服务必备）
      - /run/systemd/system:/run/systemd/system
      - /run/dbus/system_bus_socket:/run/dbus/system_bus_socket
      - /bin/systemctl:/bin/systemctl:ro
      - /bin/journalctl:/bin/journalctl:ro
      - /etc/systemd/system:/etc/systemd/system:ro
      # 挂载硬件接口（读取温度与 GPU 状态）
      - /sys:/sys:ro
      - /dev/dri:/dev/dri:ro
    privileged: true
```

### 2. 启动容器

```bash
docker compose up -d
```

启动后即可通过浏览器访问：`http://<您的宿主机IP>:8080`。

---

## 🔑 初次使用指南

1. **登录**：
   - 默认账号：`admin`
   - 默认密码：`admin123`
   *(首次登录后，可在设置页最下方修改为您自己的密码)*
2. **勾选要管理的服务**：
   - 点击右上角设置（齿轮）图标；
   - 列表中会显示宿主机上的服务，找到您想要管理的服务并打勾，右侧输入方便识别的显示名称；
   - 点击「保存纳管清单」。
3. **日常控制**：
   - 返回首页，即可看到已纳管的服务卡片，进行启停、自启控制以及查看日志。

---

## 📄 开源许可

本项目遵循 [MIT License](LICENSE) 许可协议。
