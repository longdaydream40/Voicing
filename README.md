<div align="center">

<img src="android/voice_coding/assets/icons/icon_1024.png" width="120" alt="Voicing" style="border-radius: 50%;">

# Voicing

**把手机语音输入法的输出结果塞进电脑 Agent 的嘴里**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/kevinlasnh/Voicing)](https://github.com/kevinlasnh/Voicing/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20Android-blueviolet)](#)
[![Version](https://img.shields.io/badge/version-2.9.0-green)](#)

和 AI 对话时打字太慢？Voicing 让你用嘴代替手

</div>

---

> **说明**：macOS 和 Linux 桌面端目前仍处于内测阶段，正在持续测试中，稳定性暂时无法保证。

## 它能做什么

Voicing 把手机的语音输入法变成电脑的"嘴"——你在手机上说话，文字直接出现在电脑光标处

- **零配置连接** — 手机连电脑热点，打开 App，自动连接
- **扫码直连** — 公司网络 UDP 广播失败时，扫描 PC 端二维码即可保存设备并下次自动连接
- **跨子网自动恢复** — 扫码保存同一台 PC 的多个候选 IP，热点和公司/学校局域网切换后自动重连
- **物理网卡优先** — 双端尽量绕开 VPN/代理虚拟网卡，优先走真实 WiFi/LAN
- **语音自动发送** — 说完话文字自动打过去，不需要手动操作
- **自动 Enter** — 可选开关，开启后说完话文字就被自动提交给 Agent 执行，无需手动在键盘上按回车键
- **手动发送也行** — 按回车手动发送，适合需要编辑的场景
- **撤回支持** — 发错了？一键撤回上次输入
- **断线自动恢复** — 手机息屏再亮屏，优先保持已连接显示并快速恢复
- **跨平台** — 支持 Windows / macOS / Linux 桌面端，Android 手机端
- **体积小巧** — APK 21MB，桌面端 50MB 左右，无运行时依赖

## 快速开始

### 1. 下载

从 [Releases](https://github.com/kevinlasnh/Voicing/releases/latest) 下载对应平台文件：

| 平台 | 文件 | 要求 |
|------|------|------|
| Windows | `voicing-windows-x64.exe` | Win 10/11 (64-bit) |
| macOS | `voicing-macos-arm64.dmg` | Apple Silicon (M1+) |
| Linux | `voicing-linux-x86_64` | Ubuntu 22.04+ GNOME X11 |
| Android | `voicing.apk` | Android 5.0+ |

Release 里同时提供 `SHA256SUMS.txt`，下载后可先校验 SHA-256 摘要再安装或运行。

### 2. 连接

```
电脑运行桌面端程序 → 开启热点 / 互联网共享 / 同一局域网 → 手机连接网络 → 打开 voicing App
```

- **Windows**：运行 `voicing-windows-x64.exe`，开启"移动热点"
- **macOS**：打开 `voicing-macos-arm64.dmg`，拖入 Applications（首次打开需右键→打开），开启"互联网共享"或连接同一局域网
- **Linux**：`chmod +x voicing-linux-x86_64` 后运行，开启 Wi-Fi 热点或连接同一局域网

状态栏显示"已连接"就说明连上了

如果公司、学校或宿舍网络把 UDP 广播隔离了，电脑端托盘菜单点“显示 Q R 码”，手机端点“更多功能操作”里的“扫码连接”。扫码成功后手机会记住这台电脑，下次启动会先尝试 UDP，失败后自动尝试保存过的地址候选。

### 3. 使用

1. 电脑上把光标点到要输入的位置
2. 手机上切换到语音输入法，开始说话
3. 文字自动出现在电脑上

> **推荐搭配**：[豆包输入法](https://shurufa.doubao.com/) + [大疆 Mic Mini](https://www.dji.com/cn/mic-mini) + [DJI Mic 系列手机接收器](https://store.dji.com/cn/product/dji-mic-series-mobile-receiver?vid=200571) —— 语音识别准确，领夹麦克风直连手机，体验最佳

## 功能一览

### 手机端

- 语音输入完成后自动发送到电脑
- 按回车手动发送
- "自动 Enter"开关：语音分段输入时只在静默后统一按一次回车（默认关闭）
- "撤回上次输入"恢复刚才的文本
- "刷新连接"手动重连

### 电脑端

托盘图标菜单（Windows 右键 / macOS+Linux 左键）：

| 菜单项 | 功能 |
|--------|------|
| 显示 Q R 码 | 展示当前电脑的 Voicing 配对二维码 |
| 同步输入 | 开关是否接收手机文字 |
| 开机自启 | 注册表方式，开机自动启动 |
| 打开日志 | 用记事本打开当天日志 |
| 退出应用 | 关闭程序 |

托盘图标状态：
- 闪烁 = 等待手机连接
- 常亮 = 已连接
- 灰色 = 同步已关闭

## 工作原理

1. 桌面端按可用物理网络接口分别发送 UDP 广播（端口 9530），同时覆盖热点和同一路由器局域网
2. 手机监听广播，发现桌面端后通过 WebSocket（端口 9527）建立连接
3. 如果 UDP 被企业/学校网络隔离，手机可扫描电脑端 QR，保存 `device_id` 和多个可达 IP 候选
4. 后续启动时手机优先等待 UDP 广播，失败后自动尝试已保存的地址候选
5. Android 端 WebSocket 优先绑定物理 WiFi Network，PC 端过滤 VPN/虚拟网卡，降低双端开代理时的误路由
6. 手机上的文字（语音输入或手动输入）实时发送到桌面端
7. 桌面端通过剪贴板粘贴文本（Windows Ctrl+V / macOS Cmd+V / Linux Ctrl+V），并在需要时补发一次 Enter

## 开发

### 环境准备

```bash
git clone https://github.com/kevinlasnh/Voicing.git
cd Voicing

# 桌面端（Windows / macOS / Linux）
cd pc
pip install -r requirements.txt
python voice_coding.py --dev

# Android 端
cd android/voice_coding
flutter pub get
flutter run
```

### 项目结构

```
Voicing/
├── pc/                          # 桌面端 (Python + PyQt5)
│   ├── voice_coding.py          # 主程序
│   ├── device_identity.py       # PC device_id / name / os 持久化
│   ├── platform_utils.py        # 平台检测与通用工具
│   ├── platform_keyboard.py     # 键盘模拟抽象
│   ├── platform_autostart.py    # 开机自启抽象
│   ├── platform_instance.py     # 单实例检测抽象
│   ├── voicing_protocol.py      # 协议常量
│   ├── network_recovery.py      # UDP 广播恢复逻辑
│   └── requirements.txt         # Python 依赖
├── android/voice_coding/        # Android 端 (Flutter)
│   ├── lib/
│   │   ├── main.dart            # UI 层
│   │   ├── voicing_connection_controller.dart  # 连接状态机
│   │   ├── voicing_protocol.dart               # 协议常量
│   │   ├── saved_server.dart    # 已配对 PC 持久化
│   │   ├── voicing_websocket.dart # Android WiFi-bound WebSocket / Dart fallback
│   │   ├── app_theme.dart       # 主题与设计 token
│   │   └── app_logger.dart      # 日志封装
│   └── pubspec.yaml             # Flutter 依赖
├── protocol/                    # 双端共享协议契约
│   └── voicing_protocol_contract.json
├── .github/workflows/
│   └── release.yml              # 自动构建发布
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

### 打包发布

正式发布通过 GitHub Actions 自动构建（四平台：Android / Windows / macOS / Linux）：

```bash
git tag v2.9.0
git push origin v2.9.0
```

本地调试用：

```bash
# Windows
cd pc && pyinstaller --onefile --windowed --name=Voicing \
  --icon=assets/icon.ico --add-data "assets;assets" voice_coding.py

# macOS（生成 .app bundle）
cd pc && pyinstaller --windowed --name=Voicing \
  --icon=assets/icon.icns --add-data "assets:assets" voice_coding.py

# Linux
cd pc && pyinstaller --onefile --name=Voicing \
  --add-data "assets:assets" voice_coding.py

# Android
cd android/voice_coding && flutter build apk --release
```

注意：本地 Android release 构建需要兼容的 JDK 17/21，并配置正式签名；当前 GitHub Actions 发布环境固定使用 Java 17，正式 Release 也会强制校验签名 secrets。

## 常见问题

**手机无法连接电脑？**
1. 确认电脑和手机在同一个 WiFi 热点或局域网下
2. 检查电脑防火墙是否放行 UDP 9530 和 TCP 9527
3. 如果同一 WiFi 下仍连不上，可能是公司/学校网络隔离了广播；用电脑端“显示 Q R 码”和手机端“扫码连接”配对一次
4. 手机息屏恢复后会立即进入快速重连，通常无需手动刷新
5. 仍然不行就点手机端"刷新连接"

**本地 Flutter 打 APK 失败，提示 Java / Gradle 不兼容？**
本机如果默认使用 Java 25，`flutter build apk --release` 会失败。请安装 JDK 17/21，并在 `android/voice_coding/android/local.properties` 中设置 `org.gradle.java.home=...`；正式 release 走 GitHub Actions 的 Java 17 环境。

**文字打到了错误位置？**
发送前确保电脑光标在正确的输入框里

**日志在哪？**
右键（macOS/Linux 为左键）托盘图标 → "打开日志"
- Windows: `%APPDATA%\Voicing\logs\`
- macOS: `~/Library/Logs/Voicing/`
- Linux: `~/.local/share/Voicing/logs/`

## 贡献

欢迎提交 Issue 和 Pull Request，请看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

[MIT License](LICENSE)
