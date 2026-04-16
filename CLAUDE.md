# Voicing 开发规范

## 当前状态（2026-04-16）

- 当前版本：`v2.8.0`
- 最新 Release：`https://github.com/kevinlasnh/Voicing/releases/tag/v2.8.0`
- 最新构建产物：
  - `voicing.apk`（Android）
  - `voicing-windows-x64.exe`（Windows）
  - `voicing-macos-arm64.dmg`（macOS Apple Silicon）
  - `voicing-linux-x86_64`（Ubuntu 24.04+ GNOME X11）
- 桌面端架构：平台抽象层（`platform_utils` / `platform_keyboard` / `platform_autostart` / `platform_instance`）
- 传输架构：Windows/Linux 走经典蓝牙 RFCOMM，macOS 走 WiFi（UDP + WebSocket）
- Android 息屏亮屏恢复：前台恢复窗口 + UDP 监听重建 + 快速重连
- 自动 Enter：`submit / shadow / commit` 三段式协议，避免语音分段时多次回车

## ⚠️ 强制规则

### 每次代码修改后必须更新 CHANGELOG

**以下情况必须撰写 CHANGELOG：**
- 代码有功能改动（新增、修改、删除功能）
- Bug 修复
- UI/UI 样式变更
- 配置文件变更
- 依赖库版本变更

**流程：**
1. 修改代码
2. **立即更新 CHANGELOG.md**
3. Git commit
4. Git push

### PC 端代码修改后必须热重启

**修改 PC 端代码 (`pc/voice_coding.py`) 后，必须强制进行热重启操作！**

**热重启命令：**
```powershell
powershell -ExecutionPolicy Bypass -File ".claude/skills/pc-hot-restart/restart_pc_dev.ps1"
```

**原因**：PC 端是 Python 长期运行的进程，修改代码后不会自动生效，必须手动重启。

### Flutter 构建必须使用 Java 17/21

**问题**：系统 JAVA_HOME 可能指向不兼容的 Java 版本（如 Java 25），导致 Gradle 构建失败。

**错误特征**：
```
Error resolving plugin [id: 'dev.flutter.flutter-plugin-loader', version: '1.0.0']
> 25.0.1
```
这里的 `25.0.1` 是 Java 版本号，说明使用了不兼容的 Java 版本。

**当前现状**：
- 本机 `flutter doctor --verbose` 显示 Android toolchain 正在使用 Java 25
- 本地 `flutter build apk --release` 会因 Java 25 / Gradle 兼容性失败
- GitHub Actions 发布环境使用 Java 17，`v2.8.0` APK 已成功构建

**解决方案**：安装兼容的 JDK 17/21，并在 `android/voice_coding/android/local.properties` 中指定 Java 路径（此文件不提交到 Git）：
```properties
org.gradle.java.home=C:\\path\\to\\jdk-17-or-21
```

**注意**：不要在 `gradle.properties` 中设置本地路径，否则会导致 CI 构建失败。

**Flutter 启动命令（PowerShell）**：
```powershell
cd C:\Zero\Doc\Cloud\GitHub\Voicing\android\voice_coding
flutter run
```

---

## 项目架构

### 桌面端 (Python + PyQt5) — 支持 Windows / macOS / Linux
- **主程序**: `pc/voice_coding.py`
- **蓝牙服务器**: `pc/bluetooth_server.py`
- **平台抽象层**:
  - `pc/platform_utils.py` — 平台检测、路径、文件打开、字体
  - `pc/platform_keyboard.py` — 键盘模拟（Enter + 粘贴，macOS 用 Cmd+V）
  - `pc/platform_autostart.py` — 开机自启（注册表 / LaunchAgents / XDG）
  - `pc/platform_instance.py` — 单实例检测（Mutex / flock）
- **协议**: `pc/voicing_protocol.py`
- **网络恢复**: `pc/network_recovery.py`
- **依赖**: `pc/requirements.txt`

### Android 端 (Flutter)
- **主程序**: `android/voice_coding/lib/main.dart`
- **连接状态机**: `android/voice_coding/lib/voicing_connection_controller.dart`
- **蓝牙控制器**: `android/voice_coding/lib/bluetooth_connection_controller.dart`
- **蓝牙桥接**: `android/voice_coding/lib/bluetooth_bridge.dart`
- **恢复策略**: `android/voice_coding/lib/connection_recovery_policy.dart`
- **协议常量**: `android/voice_coding/lib/voicing_protocol.dart`
- **依赖**: `android/voice_coding/pubspec.yaml`

---

## 开发命令

### PC 端热重启
```powershell
powershell -ExecutionPolicy Bypass -File ".claude/skills/pc-hot-restart/restart_pc_dev.ps1"
```

### PC 端打包
```bash
cd pc
pyinstaller --onefile --windowed --name=VoiceCoding voice_coding.py
```

### Android 端运行
```bash
cd android/voice_coding
flutter run
```

### Android 端验证
```bash
cd android/voice_coding
flutter test
flutter analyze --no-fatal-infos --no-fatal-warnings
```

### 桌面端验证
```bash
cd pc
python -m unittest discover -s tests
python -m py_compile voice_coding.py bluetooth_server.py network_recovery.py voicing_protocol.py platform_utils.py platform_keyboard.py platform_autostart.py platform_instance.py
```

---

## 当前协议约束（v2.8.0）

- `TYPE_TEXT` 现在带 `send_mode`
  - `submit`：普通手动发送，可选 `auto_enter`
  - `shadow`：语音分段增量发送，不直接触发 Enter
  - `commit`：只提交 Enter，不重复输入文本
- `ack` 现在带 `clear_input`
  - 仅 `submit` 由服务端确认后清空输入框
  - `shadow / commit` 改为客户端自己控制 finalize 与清空时机
- 蓝牙传输元数据：
  - `service_uuid = 8b3e3f4b-6f8f-4f2f-9d5d-77f4f84f9d11`
  - `rfcomm_channel = 11`
  - `message_delimiter = \n`

---

## 设计规范

### 颜色
- 背景深色: `#3D3B37`
- 文字白色: `#ECECEC`
- 成功绿色: `#5CB87A`
- 警告橙色: `#E5A84B`
- 错误红色: `#E85C4A`
- 灰色占位: `#6B6B6B`

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

## CI/CD 规则 (GitHub Actions)

### ⚠️ Android Gradle 构建配置

**问题根源**: GitHub Actions runner 网络环境特殊，配置不当会导致 Gradle 下载失败。

**必须遵守的规则**:

1. **gradle.properties 不能包含本地代理配置**
   ```gradle
   # ❌ 错误 - 会导致 CI 构建失败
   systemProp.https.proxyHost=127.0.0.1
   systemProp.https.proxyPort=7890
   ```

2. **gradle-wrapper.properties 使用官方源**
   ```properties
   # ✅ 正确
   distributionUrl=https\://services.gradle.org/distributions/gradle-8.12-all.zip
   ```

3. **Gradle wrapper 文件必须提交到仓库**
   - `android/voice_coding/gradlew`
   - `android/voice_coding/gradlew.bat`
   - `android/voice_coding/gradle/wrapper/gradle-wrapper.jar`
   - `android/voice_coding/gradle/wrapper/gradle-wrapper.properties`

4. **GitHub Actions workflow 配置**
   ```yaml
   - name: Set up Java
     uses: actions/setup-java@v4
     with:
       distribution: 'zulu'
       java-version: '17'

   - name: Set up Flutter
     uses: subosito/flutter-action@v2
     with:
       flutter-version: 3.27.0
       cache: true

   - name: Build APK
     run: flutter build apk --release
   ```

**常见错误**: `java.net.ConnectException: Connection refused`
- 原因: gradle.properties 配置了本地代理
- 解决: 删除代理配置或使用 `gradle.properties` 模板文件

---

## 历史开发状态 (2026-02-04)

### ✅ 已完成功能

#### PC 端托盘图标优化 (v2.3.0 → v2.7.0 跨平台)
- **圆形图标**：256px 高清，圆形外轮廓
- **图标缓存**：预缓存 normal/dim/paused 三种状态，闪烁均匀
- **悬停提示**：鼠标悬停显示 "Voicing"
- **左键+右键均可触发菜单**：适配 Windows（右键习惯）和 macOS/Linux（左键习惯）
- **菜单预加载**：首次打开快速
- **菜单方向自适应**：Windows 向上弹，macOS/Linux 向下弹

#### PC 端托盘菜单 (v1.8.0)
- **Windows 11 Fluent Design 风格** - 完整实现
- **悬停高亮效果** - 使用 `paintEvent` + `WA_TransparentForMouseEvents` 解决
- **日志系统** - 日志文件位于各平台标准路径：
  - Windows: `%APPDATA%\Voicing\logs\`
  - macOS: `~/Library/Logs/Voicing/`
  - Linux: `~/.local/share/Voicing/logs/`
- **菜单项**:
  - 📡 同步输入（开关）
  - 🚀 开机自启（开关）
  - 📋 打开日志
  - 🚪 退出应用

#### 关键技术实现

**PyQt5 悬停高亮解决方案** (重要！):
```python
# 问题：PyQt5 自定义 QWidget 的 :hover CSS 伪状态不工作
# 解决方案：

# 1. 使用 paintEvent 手动绘制背景
def paintEvent(self, event):
    painter = QPainter(self)
    if self._hovered:
        painter.setBrush(QColor(255, 255, 255, 15))
    painter.drawRoundedRect(rect, 4, 4)

# 2. 子控件必须设置鼠标事件穿透
self.icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents)

# 3. 使用 enterEvent/leaveEvent 追踪悬停状态
def enterEvent(self, event):
    self._hovered = True
    self.update()
```

### 📁 关键文件位置

| 文件 | 说明 |
|------|------|
| `pc/voice_coding.py` | 桌面端主程序（1011 行） |
| `pc/platform_utils.py` | 平台检测、路径、热点网段、字体（109 行） |
| `pc/platform_keyboard.py` | 键盘模拟抽象：Windows SendInput / macOS Cmd+V / Linux Ctrl+V（90 行） |
| `pc/platform_autostart.py` | 开机自启：注册表 / LaunchAgents / XDG autostart（137 行） |
| `pc/platform_instance.py` | 单实例检测：Mutex / flock（63 行） |
| `pc/voice_coding.py:447-500` | `MenuItemWidget` 类 - 菜单项组件 |
| `pc/voice_coding.py:570-763` | `ModernMenuWidget` 类 - 菜单容器 |
| `pc/voice_coding.py:766-878` | `ModernTrayIcon` 类 - 托盘图标 |
| `pc/voice_coding.py:100-123` | `setup_logging()` 日志配置 |

### 🔧 开发工具

**PC 热重启命令**:
```powershell
powershell -ExecutionPolicy Bypass -File ".claude/skills/pc-hot-restart/restart_pc_dev.ps1"
```

### ⚠️ 注意事项

1. **不要使用 QSS :hover** - PyQt5 自定义 QWidget 不支持
2. **子控件必须穿透鼠标事件** - 否则 enterEvent/leaveEvent 不会触发
3. **使用 state.tray_icon** - 不要传 None 给 update_tray_icon_pyqt()

