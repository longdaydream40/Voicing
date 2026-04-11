class ConnectionRecoveryPolicy {
  const ConnectionRecoveryPolicy({
    this.heartbeatTimeout = const Duration(seconds: 30),
    this.udpReconnectCooldown = const Duration(seconds: 3),
  });

  final Duration heartbeatTimeout;
  final Duration udpReconnectCooldown;

  bool shouldForceReconnectOnResume() {
    return true;
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

    if (lastConnectStartedAt == null) {
      return true;
    }

    return now.difference(lastConnectStartedAt) >= udpReconnectCooldown;
  }
}

enum ConnectionStatus {
  disconnected,
  connecting,
  connected,
}
