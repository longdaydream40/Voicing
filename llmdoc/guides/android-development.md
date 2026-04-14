# 如何进行 Android 端开发

## 开发环境准备

1. 安装 Flutter stable（CI 当前锁定 3.27.0）
2. 安装 Android SDK
3. 使用 Java 17 或 21
4. 如本机 Java 版本不兼容，可在本地未跟踪的 `android/voice_coding/android/local.properties` 中设置：

```properties
org.gradle.java.home=C:\\dev\\java21\\jdk-21.0.2
```

## 运行和调试

```powershell
cd C:\Zero\Doc\Cloud\GitHub\Voicing\android\voice_coding
flutter pub get
flutter run
```

## 推送前测试

```powershell
cd C:\Zero\Doc\Cloud\GitHub\Voicing\android\voice_coding
flutter test test/connection_recovery_policy_test.dart
flutter analyze --no-fatal-infos --no-fatal-warnings
```

## 关键代码位置

| 功能 | 文件 |
|------|------|
| 应用入口和 UI | `android/voice_coding/lib/main.dart` |
| 连接恢复策略 | `android/voice_coding/lib/connection_recovery_policy.dart` |
| Android 连接恢复测试 | `android/voice_coding/test/connection_recovery_policy_test.dart` |
| Android 权限 | `android/voice_coding/android/app/src/main/AndroidManifest.xml` |
| 依赖和版本号 | `android/voice_coding/pubspec.yaml` |

## 连接问题排查

1. 确认 PC 端已经启动
2. 确认手机与电脑在同一移动热点
3. 查看 App 返回前台后是否自动重连
4. 如仍未恢复，检查 UDP 9530 与 WebSocket 9527 是否被防火墙拦截
