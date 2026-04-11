# 连接工作流程指南

本文档描述 Android 端与 PC 端建立连接、保活、恢复连接的完整流程。

## 典型连接流程

1. **PC 端启动**：启动 WebSocket 服务器（9527）和 UDP 广播（9530）。
2. **Android 启动**：启动 UDP 监听，并立即发起一次 WebSocket 连接。
3. **自动发现**：Android 收到 UDP 广播后，更新服务器地址。
4. **连接建立**：PC 返回 `connected` 消息，Android 更新 UI 状态为“已连接”。

## 自动发现工作原理

PC 端每 2 秒广播以下消息：

```json
{"type": "voice_coding_server", "ip": "192.168.137.1", "port": 9527, "name": "主机名"}
```

Android 端监听 `0.0.0.0:9530`，收到广播后：
- 如果服务器地址变化，立即切换到新地址并重连
- 即使服务器地址没有变化，只要当前未连接，也允许广播触发恢复重连

PC 端在每轮广播前都会重新检测热点 IP，避免电脑网络恢复后继续广播旧地址。

相关实现：
- `pc/voice_coding.py` `start_udp_broadcast()`
- `pc/network_recovery.py`
- `android/voice_coding/lib/main.dart` `_startUdpDiscovery()`
- `android/voice_coding/lib/main.dart` `_handleUdpDiscovery()`

## 断线重连机制

Android 端断线处理流程：
1. `onError` 或 `onDone` 触发 `_handleDisconnect()`
2. 状态切换为 `disconnected`
3. 启动指数退避重连（3s → 6s → 12s → 24s → 30s 上限）
4. 定时器到期后重新调用 `_connect()`

为了避免休眠恢复后的假连接：
- 应用回到前台时，会直接强制重建 WebSocket 连接
- 连接建立使用 8 秒超时，避免卡在 `connecting`
- 旧 socket 的回调不会再覆盖新连接状态

相关实现：
- `android/voice_coding/lib/main.dart` `didChangeAppLifecycleState()`
- `android/voice_coding/lib/main.dart` `_forceReconnect()`
- `android/voice_coding/lib/main.dart` `_connect()`
- `android/voice_coding/lib/connection_recovery_policy.dart`

## 心跳保活机制

心跳机制用于判断连接是否仍然有效，并同步 PC 端同步开关状态：

- **Android → PC**：发送 `{"type": "ping"}`
- **PC → Android**：响应 `{"type": "pong", "sync_enabled": true}`

如果超过 30 秒没有收到 `pong`，Android 端会主动判定连接失效并进入重连流程。

相关实现：
- `pc/voice_coding.py` `handle_client()`
- `android/voice_coding/lib/main.dart` `_checkHeartbeat()`
- `android/voice_coding/lib/connection_recovery_policy.dart`

## 推送前测试

Android 端：

```bash
cd android/voice_coding
flutter test test/connection_recovery_policy_test.dart
```

PC 端：

```bash
cd pc
python -m unittest tests.test_network_recovery
```
