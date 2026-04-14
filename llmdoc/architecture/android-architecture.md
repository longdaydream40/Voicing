# Android 端架构

## 1. Identity

- **What it is**: 基于 Flutter 的移动端客户端。
- **Purpose**: 接收用户语音/文本输入，并通过 WebSocket 实时同步到 PC 端。

## 2. Core Components

- `android/voice_coding/lib/main.dart`
  - `VoicingApp`: 应用入口
  - `_MainPageState`: 仅负责 UI、菜单动画与输入区域组合
- `android/voice_coding/lib/voicing_connection_controller.dart`
  - `VoicingConnectionController`: WebSocket、UDP、心跳、自动发送、偏好设置与重连状态机
- `android/voice_coding/lib/voicing_protocol.dart`
  - 协议常量、消息构造、UDP 广播解析
- `android/voice_coding/lib/app_logger.dart`
  - Android 端运行日志入口，替代 `print`
- `android/voice_coding/lib/app_theme.dart`
  - 主题与设计 token
- `android/voice_coding/lib/connection_recovery_policy.dart`
  - 连接恢复决策：前台恢复、心跳超时、UDP 恢复重连冷却窗口
- `android/voice_coding/test/connection_recovery_policy_test.dart`
  - Android 连接恢复测试
- `android/voice_coding/test/voicing_protocol_contract_test.dart`
  - Android 协议契约测试
- `android/voice_coding/pubspec.yaml`
  - Flutter 依赖与版本号

## 3. Execution Flow

### 应用启动

1. 启动 `VoiceCodingApp`
2. `MainPage` 初始化菜单动画与 `VoicingConnectionController`
3. 控制器加载偏好设置、启动 UDP 发现监听
4. 控制器立即触发一次 `_forceReconnect()`

### WebSocket 连接

1. `VoicingConnectionController._connect()` 为当前连接分配新的 generation
2. 关闭旧 channel，清理心跳状态
3. 使用 `IOWebSocketChannel.connect()` 发起连接，并设置 8 秒超时
4. 收到 `connected` 消息后切换为 `connected`
5. 收到 `ack` 时清空输入框
6. 收到 `pong` / `sync_state` / `sync_disabled` 时刷新 `_syncEnabled`

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
- **连接状态机下沉**：把网络和自动发送逻辑从 UI 中抽离，降低 `main.dart` 复杂度。
- **协议常量集中化**：避免 Android 与 PC 再次出现消息名漂移。
- **UDP 作为恢复信号**：即使 IP 不变，只要客户端当前未连上，也允许 UDP 广播把连接拉回来。
