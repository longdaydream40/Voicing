# PC 端架构

## 1. Identity

- **What it is:** Python 系统托盘应用。
- **Purpose:** 作为 WebSocket 服务器接收手机端文本，并在当前光标位置输入。

## 2. Core Components

- `pc/voice_coding.py`
  - `AppState`: 全局运行状态
  - `start_udp_broadcast()`: UDP 自动发现广播
  - `handle_client()`: WebSocket 客户端处理
  - `type_text()`: 剪贴板粘贴式文本输入
  - `ModernTrayIcon` / `ModernMenuWidget`: 托盘 UI
- `pc/network_recovery.py`
  - `refresh_hotspot_ip()`: 热点地址变化检测
  - `build_udp_broadcast_payload()`: 广播消息构造
- `pc/tests/test_network_recovery.py`
  - EXE 侧连接恢复逻辑测试

## 3. Execution Flow

### 应用启动

1. 初始化日志系统
2. 计算热点 IP
3. 启动 WebSocket 线程
4. 启动 UDP 广播线程
5. 启动 PyQt5 托盘

### UDP 广播

1. 每轮广播前刷新热点 IP
2. 如果 IP 变化，记录日志
3. 使用最新 IP 构造 `voice_coding_server` 广播包
4. 广播到 `<broadcast>:9530`

### WebSocket 处理

1. Android 客户端接入后加入 `connected_clients`
2. PC 发送 `connected`
3. 收到 `text` 时用 `asyncio.to_thread(type_text, text)` 异步输入
4. 收到 `ping` 时返回 `pong`
5. 同步开关变化时向所有客户端广播 `sync_state`

## 4. Design Rationale

- **独立线程**：网络服务不会阻塞 PyQt5 主线程。
- **剪贴板粘贴**：保证 Unicode 输入兼容性。
- **动态刷新热点 IP**：电脑网络恢复后仍能把正确地址广播给手机端。
- **辅助模块可单测**：把恢复逻辑下沉到 `network_recovery.py`，避免测试依赖 PyQt5 或打包产物。
