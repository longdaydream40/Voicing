class ConnectionRecoveryPolicy {
  const ConnectionRecoveryPolicy({
    this.heartbeatTimeout = const Duration(seconds: 30),
    this.udpReconnectCooldown = const Duration(seconds: 3),
    this.foregroundRecoveryWindow = const Duration(seconds: 12),
    this.foregroundReconnectDelay = const Duration(milliseconds: 500),
    this.foregroundConnectTimeout = const Duration(seconds: 2),
    this.normalConnectTimeout = const Duration(seconds: 8),
    this.maxReconnectDelay = const Duration(seconds: 30),
  });

  final Duration heartbeatTimeout;
  final Duration udpReconnectCooldown;
  final Duration foregroundRecoveryWindow;
  final Duration foregroundReconnectDelay;
  final Duration foregroundConnectTimeout;
  final Duration normalConnectTimeout;
  final Duration maxReconnectDelay;

  bool shouldForceReconnectOnResume() {
    return true;
  }

  DateTime startForegroundRecovery(DateTime now) {
    return now.add(foregroundRecoveryWindow);
  }

  bool isForegroundRecoveryActive({
    required DateTime? recoveryUntil,
    required DateTime now,
  }) {
    return recoveryUntil != null && now.isBefore(recoveryUntil);
  }

  bool isHeartbeatExpired({
    required ConnectionStatus status,
    required DateTime? lastPong,
    required DateTime now,
  }) {
    if (status != ConnectionStatus.connected || lastPong == null) {
      return false;
    }

    return now.difference(lastPong) > heartbeatTimeout;
  }

  bool shouldReconnectFromUdp({
    required bool serverChanged,
    required bool foregroundRecoveryActive,
    required ConnectionStatus status,
    required DateTime? lastConnectStartedAt,
    required DateTime now,
  }) {
    if (serverChanged) {
      return true;
    }

    if (status == ConnectionStatus.connected) {
      return false;
    }

    if (foregroundRecoveryActive) {
      return true;
    }

    if (lastConnectStartedAt == null) {
      return true;
    }

    return now.difference(lastConnectStartedAt) >= udpReconnectCooldown;
  }

  Duration reconnectDelay({
    required int reconnectAttempt,
    required bool foregroundRecoveryActive,
  }) {
    if (foregroundRecoveryActive) {
      return foregroundReconnectDelay;
    }

    final delaySec = reconnectAttempt < 5
        ? 3 * (1 << reconnectAttempt)
        : maxReconnectDelay.inSeconds;
    return Duration(
      seconds: delaySec.clamp(3, maxReconnectDelay.inSeconds),
    );
  }

  Duration resolveConnectTimeout({
    required bool foregroundRecoveryActive,
  }) {
    if (foregroundRecoveryActive) {
      return foregroundConnectTimeout;
    }

    return normalConnectTimeout;
  }
}

enum ConnectionStatus {
  disconnected,
  connecting,
  connected,
}
