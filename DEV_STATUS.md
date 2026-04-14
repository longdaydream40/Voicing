# 开发状态 (Development Status)

> 最后更新：2026-04-14

## v2.5.1 已发布

**最新 Release**: [v2.5.1](https://github.com/kevinlasnh/Voicing/releases/tag/v2.5.1)

已发布文件：
- `voicing.apk` - Android 安装包
- `voicing.exe` - Windows 电脑端

---

## 已完成功能

### 核心功能
- [x] WebSocket 实时通信 (PC:9527)
- [x] UDP 自动发现 (端口 9530)
- [x] Android 文字输入 + 发送
- [x] Android 撤回功能
- [x] 自动发送（语音输入实时同步）
- [x] PC 端自动输入到光标位置
- [x] Windows 11 托盘菜单
- [x] 日志系统
- [x] 开机自启
- [x] 心跳保活 + 自动断线重连

### 稳定性修复
- [x] Android 生命周期处理（`paused` / `resumed`）
- [x] Android 休眠恢复后强制重建连接
- [x] Android WebSocket 连接超时（8 秒）
- [x] Android 旧连接回调隔离，防止 stale socket 覆盖新状态
- [x] Android 同 IP UDP 广播恢复重连
- [x] PC 端 UDP 广播每轮刷新热点 IP
- [x] PC 端异步非阻塞输入（`asyncio.to_thread()`）

### 文档与测试
- [x] CHANGELOG 更新到 v2.5.1
- [x] README / llmdoc / Android 文档同步更新
- [x] 自动发送功能硬编码为始终启用，移除手动开关
- [x] Android 连接恢复策略测试
- [x] PC 广播恢复逻辑测试
- [x] Android / PC 协议契约测试
- [x] Android `main.dart` 架构拆分（协议 / 日志 / 连接控制器 / UI）

---

## 推送前验证

### Android
```bash
cd android/voice_coding
flutter test test/connection_recovery_policy_test.dart test/voicing_protocol_contract_test.dart
flutter analyze --no-fatal-infos --no-fatal-warnings
```

### PC
```bash
cd pc
python -m unittest tests.test_network_recovery tests.test_protocol_contract
python -m py_compile voice_coding.py network_recovery.py voicing_protocol.py
```

---

## GitHub Actions 发布流程

```bash
git add .
git commit -m "chore: release v2.5.1"
git tag v2.5.1
git push origin main
git push origin v2.5.1
```

标签推送后由 `.github/workflows/release.yml` 自动构建 APK 和 EXE，并创建 GitHub Release。

本次发布验证结果：
- Android tests: pass
- Android analyze: pass
- PC tests: pass
- PC py_compile: pass
- Release: success

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.5.1 | 2026-04-14 | 自动发送硬编码启用、Android UI 优化、PC 菜单首次右键卡顿修复 |
| v2.5.0 | 2026-04-14 | 协议契约测试、Android 架构拆分、CI/文档修复、自动发送开关间距优化 |
| v2.4.2 | 2026-04-11 | 修复休眠唤醒后的假断连，补充连接恢复测试 |
| v2.4.1 | 2026-04-08 | UI 优化（设计常量、触摸反馈、菜单分组、键盘支持） |
| v2.4.0 | 2026-04-08 | 全栈优化（断连修复、异步阻塞、代码清理） |
| v2.3.1 | 2026-02-04 | 网络权限 + EXE 图标修复 |
