# Voicing 技术发现记录

> 记录项目开发过程中的重要技术发现和解决方案

---

## 关键技术实现

### 1. PyQt5 悬停高亮解决方案

**问题**：PyQt5 自定义 QWidget 的 CSS `:hover` 伪状态不工作

**解决方案**：
```python
# 1. 使用 paintEvent 手动绘制背景（支持 hover + pressed 两种状态）
def paintEvent(self, event):
    painter = QPainter(self)
    if self._pressed:
        painter.setBrush(QColor(255, 255, 255, 25))  # 按压: 白色 10%
    elif self._hovered:
        painter.setBrush(QColor(255, 255, 255, 15))  # 悬停: 白色 6%
    painter.drawRoundedRect(rect, 4, 4)

# 2. 子控件必须设置鼠标事件穿透
self.icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents)

# 3. 使用 enterEvent/leaveEvent 追踪悬停状态
# 4. 使用 mousePressEvent/mouseReleaseEvent 追踪按压状态
```

**位置**：`pc/voice_coding.py` MenuItemWidget 类

---

### 2. 自动发送功能 (Shadow Mode)

**原理**：利用 Flutter 的 `TextEditingController.value.composing` 检测输入法组合状态

```dart
// composing.isValid && !composing.isCollapsed = 输入法正在输入（下划线状态）
// !isComposing = 输入完成（下划线消失）

if (_wasComposing && !isComposing) {
    _sendShadowIncrement();  // 发送增量文本
}
```

**位置**：`android/voice_coding/lib/main.dart:344-362`

---

### 3. 剪贴板方式实现 Unicode 输入

**问题**：pyautogui.type() 无法处理中文等 Unicode 字符

**解决方案**：
```python
# 1. 保存当前剪贴板
old_clipboard = pyperclip.paste()

# 2. 复制新文本到剪贴板
pyperclip.copy(text)

# 3. 模拟 Ctrl+V 粘贴
pyautogui.hotkey('ctrl', 'v')

# 4. 等待完成
time.sleep(0.1)

# 5. 恢复原剪贴板
pyperclip.copy(old_clipboard)
```

**位置**：`pc/voice_coding.py:301-335`

---

### 4. Flutter 构建 Java 版本问题

**问题**：系统 JAVA_HOME 指向 Java 25，Gradle 构建失败

**错误特征**：
```
Error resolving plugin [id: 'dev.flutter.flutter-plugin-loader', version: '1.0.0']
> 25.0.1
```

**解决方案**：
- 在 `android/voice_coding/android/local.properties` 中指定 Java 路径
- **不要**在 `gradle.properties` 中设置（会导致 CI 构建失败）

```properties
org.gradle.java.home=C:\\dev\\java21\\jdk-21.0.2
```

**本机 Java 路径**：`C:\dev\java21\jdk-21.0.2`

---

### 5. GitHub Actions Gradle 配置

**关键规则**：`gradle.properties` 不能包含本地代理配置

```gradle
# ❌ 错误 - 会导致 CI 构建失败
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=7890
```

**正确配置**：
- `gradle-wrapper.properties` 使用官方源
- Gradle wrapper 文件必须提交到仓库

---

### 6. PC 热重启

**原因**：PC 端是 Python 长期运行的进程，代码修改后不会自动生效

**热重启命令**：
```powershell
powershell -ExecutionPolicy Bypass -File ".claude/skills/pc-hot-restart/restart_pc_dev.ps1"
```

---

### 7. Android 待机断连根因与修复

**问题**：手机待机后亮屏，App 显示"未连接"，但 WiFi 仍连着热点

**根因链**：
1. App 只处理 `resumed` 生命周期，忽略 `paused`
2. 无主动心跳，无法检测静默断连
3. WiFi 层（L2）vs Socket 层（L4）不同步

**修复方案**：
```dart
// 心跳：每 15s 发 ping，30s 无 pong 判定死亡
Timer.periodic(Duration(seconds: 15), (_) => _checkHeartbeat());

// 生命周期：paused 停心跳，resumed 验证连接
if (state == AppLifecycleState.paused) _stopHeartbeat();
if (state == AppLifecycleState.resumed) {
  if (connected) { _sendPing(); _startHeartbeat(); }
  else { _connect(); }
}

// 指数退避：3s → 6s → 12s → 24s → 30s(上限)
final delaySec = 3 * (1 << _reconnectAttempt);
```

**位置**：`android/voice_coding/lib/main.dart`

---

### 8. PC 端 async 阻塞问题

**问题**：`type_text()` 在 async `handle_client()` 中同步调用，阻塞 WebSocket 事件循环

**修复**：
```python
# 改前（阻塞）
type_text(text)

# 改后（非阻塞）
await asyncio.to_thread(type_text, text)
```

**位置**：`pc/voice_coding.py` handle_client()

---

### 9. Flutter 设计 Token 系统

**基于 UI Skill 规范建立的设计常量**：

```dart
class AppSpacing {
  static const double xs = 4;    // 4px grid base
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double componentPadding = 14;
  static const double componentGap = 12;
  static const double borderRadius = 12;
}

class AppColors {
  static const Color surface = Color(0xFF3D3B37);
  static const Color primary = Color(0xFFD97757);
  static const Color success = Color(0xFF5CB87A);
  // ...
}
```

**规范来源**：ui-ux-pro-max + flutter-building-layouts + ui-mobile Skill

**位置**：`android/voice_coding/lib/main.dart` 文件顶部

---

### 10. Android 息屏唤醒后的二次断连根因

**现象**：手机仍连接电脑热点，但 App 在亮屏回前台后显示“未连接”，必须手动切 WiFi 才能恢复。

**二次根因**：
1. `resumed` 时仍可能继续信任休眠前旧 socket
2. WebSocket 连接没有 connect timeout，容易卡在 `connecting`
3. 旧 socket 的 `onDone` / `onError` 可能晚到，覆盖新连接状态
4. 同一台 PC 的 UDP 广播如果 IP 未变化，旧逻辑不会触发恢复重连

**修复策略**：
```dart
// 1. 前台恢复直接强制重建连接
if (state == AppLifecycleState.resumed) {
  _forceReconnect(resetBackoff: true, reason: 'app resumed');
}

// 2. 连接建立增加超时
_channel = IOWebSocketChannel.connect(
  Uri.parse('ws://$_serverIp:$_serverPort'),
  connectTimeout: const Duration(seconds: 8),
);

// 3. 用 generation 忽略旧连接回调
final int connectionId = ++_connectionGeneration;
if (connectionId != _connectionGeneration) return;
```

**相关文件**：
- `android/voice_coding/lib/main.dart`
- `android/voice_coding/lib/connection_recovery_policy.dart`

---

### 11. PC 端 UDP 广播必须每轮刷新热点 IP

**问题**：如果电脑网络恢复后热点 IP 发生变化，启动时缓存的旧 IP 会继续被广播，导致手机连错地址。

**修复**：
```python
current_hotspot_ip, hotspot_ip_changed = refresh_hotspot_ip(
    HOTSPOT_IP,
    get_hotspot_ip(),
)
HOTSPOT_IP = current_hotspot_ip
broadcast_data = build_udp_broadcast_payload(
    HOTSPOT_IP,
    state.ws_port,
    socket.gethostname(),
)
```

**测试**：
- `pc/tests/test_network_recovery.py`

---

### 12. 本次推送前测试结论

**Android**：
- `flutter test test/connection_recovery_policy_test.dart` 通过（4/4）
- `flutter analyze --no-fatal-infos --no-fatal-warnings` 无 error，仅剩 info

**PC**：
- `python -m unittest tests.test_network_recovery` 通过（3/3）
- `python -m py_compile voice_coding.py network_recovery.py` 通过

---

## 设计系统

### 颜色

| 用途 | 颜色值 |
|------|--------|
| 背景深色 | `#3D3B37` |
| 文字白色 | `#ECECEC` |
| 成功绿色 | `#5CB87A` |
| 警告橙色 | `#E5A84B` |
| 错误红色 | `#E85C4A` |
| 灰色占位 | `#6B6B6B` |
| 图标背景 | `#1A1A2E` |

### 间距

- 边缘 padding: 16px
- 组件内 padding: 14px
- 组件间距: 12px
- 圆角: 12px

### 字体

- 正文: 16px
- 状态文字: 15px, fontWeight 600
- 提示文字: 13px

---

## 通信协议

### UDP 发现 (端口 9530)

```json
{
  "type": "voice_coding_server",
  "ip": "192.168.137.1",
  "port": 9527,
  "name": "主机名"
}
```

- PC 端每 2 秒广播一次
- Android 端监听并自动连接

### WebSocket 消息类型 (端口 9527)

| 方向 | 类型 | 用途 |
|------|------|------|
| PC → Android | `connected` | 连接确认 |
| PC → Android | `ack` | 文本接收确认 |
| PC → Android | `pong` | 心跳响应 |
| PC → Android | `sync_state` | 同步状态广播 |
| PC → Android | `sync_disabled` | 同步已禁用 |
| Android → PC | `text` | 文本输入 |
| Android → PC | `ping` | 心跳请求 |

---

## 关键文件位置

| 文件 | 说明 |
|------|------|
| `pc/voice_coding.py` | PC 端主程序 (1124 行) |
| `pc/voice_coding.py:96-109` | AppState 类 |
| `pc/voice_coding.py:457-563` | MenuItemWidget 类 |
| `pc/voice_coding.py:565-740` | ModernMenuWidget 类 |
| `pc/voice_coding.py:742-851` | ModernTrayIcon 类 |
| `android/voice_coding/lib/main.dart` | Android 主程序 (789 行) |
| `.github/workflows/release.yml` | CI/CD 配置 |

---

## 依赖版本

| 端 | 技术 | 版本 |
|------|------|------|
| PC | Python | 3.12 (CI) |
| PC | PyQt5 | ~=5.15.0 |
| PC | websockets | ~=12.0 |
| Android | Flutter | 3.27.0 |
| Android | Dart | ^3.5.4 |
| Android | web_socket_channel | ^2.4.0 |

**注**：v2.4.0 移除了 pystray 依赖，requirements.txt 版本约束从 `>=` 改为 `~=`

---

## 2026-04-14 审计发现

### 1. 当前仓库与远端主线一致，但工作区非干净

- 本地 `main` 指向 `95060ab`，与 `origin/main` 一致
- 远端最新标签仍为 `v2.4.2`
- 工作区存在未提交改动：
  - `.claude/settings.local.json`
  - `android/voice_coding/android/local.properties`
  - `pc/VoiceCoding.spec`

### 2. Android 与 PC 的真实耦合方式

- 双端没有共享协议层或共享常量模块
- 当前耦合完全依赖：
  - UDP 广播发现：`9530`
  - WebSocket 通信：`9527`
  - 运行时 JSON 消息类型字符串
- 这意味着“一致性”主要靠人工同步和测试，而不是编译期约束

### 3. 已确认的协议对称点

- PC 端会发送：`connected`、`ack`、`pong`、`sync_state`、`sync_disabled`
- Android 端明确处理：`connected`、`ack`、`pong`、`sync_state`
- 双端都实现了：
  - Android `ping` / PC `pong`
  - 文本 `text`
  - `sync_enabled` 状态同步
  - 基于 UDP 的自动发现与恢复

### 4. 已发现的协议不对称点

- Android 端未显式处理 PC 端定义的 `sync_disabled` 消息
- 目前主要依赖先前的 `sync_state` / `pong` 把 `_syncEnabled` 置为 `false`，大多数场景可工作
- 但如果用户在同步关闭状态刚传播前发送文本，PC 会回 `sync_disabled`，Android 当前只会忽略该消息

### 5. 文档/声明与代码的初步差异

- `android/README.md` 声称技术栈为 `Dart 3.6.0`，而 `pubspec.yaml` 只声明 `sdk: ^3.5.4`
- `pubspec.yaml` 里写的是 `flutter_launcher_icons: ^0.14.3`，但 `pubspec.lock` 已解析到 `0.14.4`
- README / DEV_STATUS / llmdoc / CHANGELOG 目前都仍以 `v2.4.2` 为最新版本

### 6. 依赖与工具链的最新性结论

- Android 本机环境：
  - `flutter --version` = `3.24.5`
  - `Dart` = `3.5.4`
- `flutter pub outdated` 结果显示：
  - `cupertino_icons` 当前 `1.0.8`，最新 `1.0.9`
  - `shared_preferences` 当前 `2.5.3`，最新 `2.5.5`
  - `web_socket_channel` 当前 `2.4.5`，最新 `3.0.3`
  - `flutter_lints` 当前 `4.0.0`，最新 `6.0.0`
- Python 侧 `pip index versions` 结果显示：
  - `PyInstaller` 最新 `6.19.0`，当前环境已装 `6.18.0`
  - `Pillow` 最新 `12.2.0`，当前环境已装 `12.1.0`
  - `PyQt5` 最新 `5.15.11`，当前环境已装 `5.15.11`
  - `PyAutoGUI` 最新仍为 `0.9.54`
  - `pyperclip` 最新 `1.11.0`
  - `websockets` 最新 `16.0`
- 结论：仓库并非“所有内容都最新”，尤其 Flutter/Dart 与多项依赖版本说明已经落后；但不应在未做兼容性验证前盲目升大版本

### 7. 已执行的低风险修复

- **协议耦合修复**
  - PC 端 `sync_disabled` 响应加入 `sync_enabled: false`
  - Android 端显式处理 `sync_disabled`，避免同步开关状态在竞争窗口中失真
- **GitHub Actions 修复**
  - `release.yml` 现在会把 Git 标签 `v2.4.2` 映射到 `CHANGELOG.md` 的 `## [2.4.2]`
  - 若缺少对应 changelog 条目，工作流会直接失败，不再静默生成空 release notes
- **仓库卫生修复**
  - `android/voice_coding/android/local.properties` 已加入 `.gitignore`
  - 该文件已从版本控制中移除，但保留本地工作副本
- **文档同步修复**
  - 修正本地 EXE 打包命令缺少图标与资源参数的问题
  - 修正 Android README 中错误的目录、EXE 名称与 Dart/Flutter 版本描述
  - 修正 llmdoc 中 `Voice-Coding` 旧路径和 `local.properties` 跟踪方式描述

### 8. v2.5.0 的结构性优化结果

- **Android 架构**
  - 连接状态机、UDP 发现、心跳与自动发送逻辑已迁入 `voicing_connection_controller.dart`
  - `main.dart` 现仅负责界面、菜单动画和输入区域组合
  - `app_logger.dart` 已替换生产代码中的 `print`
  - `app_theme.dart` / `voicing_protocol.dart` 已把主题与协议常量抽离
- **协议耦合**
  - 仓库新增共享契约文件 `protocol/voicing_protocol_contract.json`
  - Android / PC 两端都新增契约测试，当前通过
  - 当前耦合方式仍然是“共享契约文件 + 双端测试”，不是自动生成代码；但已经明显优于原先的纯字符串散落模式
- **UI 细节**
  - Android 菜单中“自动发送”文本与开关之间已增加固定间距，避免按钮紧贴文字

### 9. 发布前最终验证结论

- Android：
  - `flutter test` 全部通过（9/9）
  - `flutter analyze --no-fatal-infos --no-fatal-warnings` 无 issue
- PC：
  - `python -m unittest discover -s tests` 全部通过（7/7）
  - `python -m py_compile voice_coding.py network_recovery.py voicing_protocol.py` 通过
  - 依赖环境已重新安装并与 `requirements.txt` 对齐
- 结论：
  - APK 与 EXE 的核心耦合链路（UDP 发现、WebSocket 端口、消息类型、关键字段）在当前仓库状态下没有发现新的协议不一致问题
  - 仍未做到“单一源码生成双端协议代码”，但已达到可发布、可维护、可回归验证的状态
