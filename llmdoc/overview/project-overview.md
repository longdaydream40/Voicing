# Voicing 项目概览

## 1. 项目简介

Voicing 是一款让手机语音输入直接出现在电脑光标位置的双端工具，适合与 AI 对话、长文输入和轻量办公场景。

当前目标版本：`v2.5.0`

## 2. 技术栈

### PC 端
- **语言**: Python 3.12（CI）/ Python 本地开发环境
- **UI**: PyQt5
- **网络**: `websockets` + `socket`
- **输入模拟**: `pyautogui` + `pyperclip`

### Android 端
- **语言**: Dart
- **框架**: Flutter stable（CI 当前锁定 3.27.0）
- **网络**: `web_socket_channel` + `RawDatagramSocket`
- **持久化**: `shared_preferences`

## 3. 核心特性

- UDP 自动发现电脑端
- WebSocket 实时文本传输
- 自动发送模式
- 心跳保活
- 指数退避重连
- 手机息屏/亮屏后的自动恢复连接
- PC 端热点 IP 动态刷新广播

## 4. 当前版本重点

### v2.5.0

- Android 端拆分为 UI / 连接控制器 / 协议 / 日志模块
- 新增 Android / PC 双端协议契约测试
- GitHub Actions release notes 提取逻辑修复
- `local.properties` 改为本地未跟踪文件
- 菜单中“自动发送”开关间距优化

## 5. 发布方式

正式发布通过 GitHub Actions 完成：

1. 更新代码与文档
2. 提交到 `main`
3. 创建并推送 `v<version>` 标签
4. GitHub Actions 自动构建 `voicing.apk` 与 `voicing.exe`
5. 自动创建 GitHub Release
