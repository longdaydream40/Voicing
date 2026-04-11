# Android 端架构

## 1. Identity

- **What it is**: 基于 Flutter 的移动端客户端。
- **Purpose**: 接收用户语音/文本输入，并通过 WebSocket 实时同步到 PC 端。

## 2. Core Components

- `android/voice_coding/lib/main.dart`
  - `VoiceCodingApp`: 应用入口与主题配置
  - `_MainPageState`: UI 状态、网络状态、输入发送逻辑
  - `_forceReconnect()`: 前台恢复和手动刷新时的统一重连入口
  - `_connect()`: WebSocket 建立与连接代次管理
  - `_handleUdpDiscovery()`: UDP 自动发现与同 IP 恢复重连
  - `_checkHeartbeat()`: ping/pong 心跳保活与超时判定
- `android/voice_coding/lib/connection_recovery_policy.dart`
  - 连接恢复决策：前台恢复、心跳超时、UDP 恢复重连冷却窗口
- `android/voice_coding/test/connection_recovery_policy_test.dart`
  - Android 连接恢复测试
- `android/voice_coding/pubspec.yaml`
  - Flutter 依赖与版本号

## 3. Execution Flow

### 应用启动

1. 启动 `VoiceCodingApp`
2. `MainPage` 初始化菜单动画、文本监听、偏好设置
3. 启动 UDP 发现监听
4. 立即触发一次 `_forceReconnect()`

### WebSocket 连接

1. `_connect()` 为当前连接分配新的 generation
2. 关闭旧 channel，清理心跳状态
3. 使用 `IOWebSocketChannel.connect()` 发起连接，并设置 8 秒超时
4. 收到 `connected` 消息后切换为 `connected`
5. 收到 `ack` 时清空输入框
6. 收到 `pong` / `sync_state` 时刷新 `_syncEnabled`

### 休眠恢复

1. `paused`：停止心跳，避免后台无意义 ping
2. `resumed`：不复用旧 socket，直接 `_forceReconnect()`
3. 如果旧 socket 晚到 `onDone` / `onError`，会因 generation 不匹配被忽略

### UDP 自动发现

1. Android 持续监听 9530 端口
2. 收到 `voice_coding_server` 后解析 IP/端口
3. 如果地址变化，立刻切换到新地址
4. 如果地址没变但当前未连接，也允许广播触发恢复重连

## 4. Design Rationale

- **强制前台重连**：解决手机息屏后 WebSocket 半死不活但 UI 未恢复的问题。
- **连接超时**：避免连接卡死在 `connecting`。
- **连接代次隔离**：避免旧连接回调污染新状态。
- **恢复策略下沉**：把关键恢复规则放进 `connection_recovery_policy.dart`，便于单测。
- **UDP 作为恢复信号**：即使 IP 不变，只要客户端当前未连上，也允许 UDP 广播把连接拉回来。
