import 'package:flutter_test/flutter_test.dart';
import 'package:voicing/connection_recovery_policy.dart';

void main() {
  const policy = ConnectionRecoveryPolicy(
    heartbeatTimeout: Duration(seconds: 30),
    udpReconnectCooldown: Duration(seconds: 3),
  );

  test('resumed always forces a reconnect', () {
    expect(policy.shouldForceReconnectOnResume(), isTrue);
  });

  test('resumed foreground recovery stays active before deadline', () {
    final now = DateTime(2026, 4, 15, 18, 0, 0);
    final recoveryUntil = policy.startForegroundRecovery(now);

    expect(
      policy.isForegroundRecoveryActive(
        recoveryUntil: recoveryUntil,
        now: now.add(const Duration(seconds: 11)),
      ),
      isTrue,
    );
    expect(
      policy.isForegroundRecoveryActive(
        recoveryUntil: recoveryUntil,
        now: now.add(const Duration(seconds: 12)),
      ),
      isFalse,
    );
  });

  test('heartbeat timeout marks connected sockets as expired', () {
    final now = DateTime(2026, 4, 11, 18, 0, 31);
    final lastPong = now.subtract(const Duration(seconds: 31));

    expect(
      policy.isHeartbeatExpired(
        status: ConnectionStatus.connected,
        lastPong: lastPong,
        now: now,
      ),
      isTrue,
    );
  });

  test('same-server UDP broadcast can recover a disconnected client after cooldown', () {
    final now = DateTime(2026, 4, 11, 18, 0, 10);
    final lastConnectStartedAt = now.subtract(const Duration(seconds: 4));

    expect(
      policy.shouldReconnectFromUdp(
        serverChanged: false,
        foregroundRecoveryActive: false,
        status: ConnectionStatus.disconnected,
        lastConnectStartedAt: lastConnectStartedAt,
        now: now,
      ),
      isTrue,
    );
  });

  test('same-server UDP broadcast does not thrash while a fresh connect is in progress', () {
    final now = DateTime(2026, 4, 11, 18, 0, 10);
    final lastConnectStartedAt = now.subtract(const Duration(seconds: 1));

    expect(
      policy.shouldReconnectFromUdp(
        serverChanged: false,
        foregroundRecoveryActive: false,
        status: ConnectionStatus.connecting,
        lastConnectStartedAt: lastConnectStartedAt,
        now: now,
      ),
      isFalse,
    );
  });

  test('same-server UDP broadcast reconnects immediately during foreground recovery', () {
    final now = DateTime(2026, 4, 15, 18, 0, 10);
    final lastConnectStartedAt = now.subtract(const Duration(seconds: 1));

    expect(
      policy.shouldReconnectFromUdp(
        serverChanged: false,
        foregroundRecoveryActive: true,
        status: ConnectionStatus.connecting,
        lastConnectStartedAt: lastConnectStartedAt,
        now: now,
      ),
      isTrue,
    );
  });

  test('foreground recovery uses fast retry and short connect timeout', () {
    expect(
      policy.reconnectDelay(
        reconnectAttempt: 3,
        foregroundRecoveryActive: true,
      ),
      const Duration(milliseconds: 500),
    );
    expect(
      policy.resolveConnectTimeout(foregroundRecoveryActive: true),
      const Duration(seconds: 2),
    );
  });

  test('regular reconnect keeps exponential backoff and normal connect timeout', () {
    expect(
      policy.reconnectDelay(
        reconnectAttempt: 2,
        foregroundRecoveryActive: false,
      ),
      const Duration(seconds: 12),
    );
    expect(
      policy.resolveConnectTimeout(foregroundRecoveryActive: false),
      const Duration(seconds: 8),
    );
  });
}
