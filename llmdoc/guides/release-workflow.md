# 如何发布新版本

正式发布以 GitHub Actions 为准，本地构建仅用于开发调试。

## 标准流程

1. 更新代码、测试和文档
2. 运行推送前测试
3. 提交变更
4. 创建 `v<version>` 标签
5. 推送 `main` 和标签
6. 在 GitHub Actions 中等待 `build-android`、`build-windows`、`release` 完成

## 命令示例

```bash
git add .
git commit -m "chore: release v2.4.2"
git tag v2.4.2
git push origin main
git push origin v2.4.2
```

## 推送前测试

### Android

```bash
cd android/voice_coding
flutter test test/connection_recovery_policy_test.dart
flutter analyze --no-fatal-infos --no-fatal-warnings
```

### PC

```bash
cd pc
python -m unittest tests.test_network_recovery
python -m py_compile voice_coding.py network_recovery.py
```

## 常见问题

### Java 版本不兼容

- 症状：Gradle 报 `25.0.1`
- 处理：本地开发时在 `android/local.properties` 设置 Java 21 路径
- 说明：CI 使用 GitHub Actions 中固定的 Java 17，不依赖本机环境

### Release 没有产物

- 检查标签是否为 `v<version>` 格式
- 检查 `CHANGELOG.md` 是否存在对应版本条目
- 检查 Actions 中 `build-android` 和 `build-windows` 是否成功
