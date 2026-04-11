# PC 端开发指南

## 开发环境设置

```bash
cd pc
pip install -r requirements.txt
python voice_coding.py --dev
```

## 热重启

```powershell
powershell -ExecutionPolicy Bypass -File ".claude/skills/pc-hot-restart/restart_pc_dev.ps1"
```

## 推送前测试

```bash
cd pc
python -m unittest tests.test_network_recovery
python -m py_compile voice_coding.py network_recovery.py
```

## 关键代码位置

| 功能 | 文件 |
|------|------|
| 主程序 | `pc/voice_coding.py` |
| UDP 恢复辅助逻辑 | `pc/network_recovery.py` |
| EXE 侧测试 | `pc/tests/test_network_recovery.py` |
| 图标和资源 | `pc/assets/` |

## 排查建议

1. 查看 `%APPDATA%\Voicing\logs\` 下的当天日志
2. 验证 9527 / 9530 端口是否可用
3. 重点关注热点 IP 是否变化，以及 UDP 广播是否仍在发送最新地址
