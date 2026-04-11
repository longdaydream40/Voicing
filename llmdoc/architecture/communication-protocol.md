# 通信协议架构

## 1. Identity

- **What it is**: PC 端与 Android 端之间的双层通信协议。
- **Purpose**: 负责服务发现、长连接传输、状态同步和连接恢复。

## 2. Core Components

- `pc/voice_coding.py` `start_udp_broadcast()`: 周期性广播服务器信息
- `pc/network_recovery.py`: 热点 IP 刷新与 UDP 广播负载生成
- `pc/voice_coding.py` `handle_client()`: WebSocket 消息处理
- `android/voice_coding/lib/main.dart` `_connect()`: WebSocket 客户端连接逻辑
- `android/voice_coding/lib/main.dart` `_handleMessage()`: WebSocket 消息处理
- `android/voice_coding/lib/main.dart` `_handleUdpDiscovery()`: UDP 广播解析与恢复重连
- `android/voice_coding/lib/connection_recovery_policy.dart`: Android 端连接恢复策略

## 3. Execution Flow

### UDP 发现流程（9530）

1. PC 端启动后持续广播 `voice_coding_server`
2. 每轮广播前重新获取热点 IP
3. Android 持续监听 9530 端口
4. Android 收到广播后更新 `_serverIp` / `_serverPort`
5. 如果当前未连接，即使 IP 不变，也允许广播触发恢复重连

### WebSocket 连接流程（9527）

1. Android 发起 `ws://<ip>:9527`
2. PC 接受连接并发送 `connected`
3. Android 记录 `connected` 状态并开始心跳
4. Android 发送 `text`
5. PC 输入文本后发送 `ack`

### 心跳与状态同步

1. Android 周期发送 `ping`
2. PC 响应 `pong`，同时带上 `sync_enabled`
3. Android 更新本地同步状态
4. 如果 30 秒没有 `pong`，Android 触发断线重连

### 休眠恢复

1. Android 进入后台时停止心跳
2. 返回前台时直接强制重连
3. 连接建立有 8 秒超时
4. 旧连接回调通过 generation 机制隔离

## 4. Message Types

### PC → Android

- `connected`
- `ack`
- `pong`
- `sync_state`
- `sync_disabled`

### Android → PC

- `text`
- `ping`

## 5. Design Rationale

- **UDP 负责发现，WebSocket 负责传输**：降低配置复杂度。
- **pong 合并同步状态**：减少额外消息数量。
- **同 IP 恢复重连**：解决“WiFi 还在，但客户端没重新连上”的场景。
- **动态广播热点 IP**：解决电脑网络恢复后继续广播旧地址的问题。
