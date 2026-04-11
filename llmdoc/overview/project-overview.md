# Voicing 项目概览

## 1. 项目简介

Voicing 是一款让手机语音输入直接出现在电脑光标位置的双端工具，适合与 AI 对话、长文输入和轻量办公场景。

当前目标版本：`v2.4.2`

## 2. 技术栈

### PC 端
- **语言**: Python 3.12（CI）/ Python 本地开发环境
- **UI**: PyQt5
- **网络**: `websockets` + `socket`
- **输入模拟**: `pyautogui` + `pyperclip`

### Android 端
- **语言**: Dart
- **框架**: Flutter 3.27.0
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

### v2.4.2

- 修复 Android 休眠唤醒后的假断连
- Android 返回前台时强制重建连接
- Android 连接建立增加 8 秒超时
- Android 同 IP UDP 广播可触发恢复重连
- PC 每轮 UDP 广播刷新热点 IP
- 新增 Android / PC 两侧连接恢复测试

## 5. 发布方式

正式发布通过 GitHub Actions 完成：

1. 更新代码与文档
2. 提交到 `main`
3. 创建并推送 `v<version>` 标签
4. GitHub Actions 自动构建 `voicing.apk` 与 `voicing.exe`
5. 自动创建 GitHub Release
