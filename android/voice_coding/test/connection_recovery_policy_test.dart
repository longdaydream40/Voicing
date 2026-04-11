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
        status: ConnectionStatus.connecting,
        lastConnectStartedAt: lastConnectStartedAt,
        now: now,
      ),
      isFalse,
    );
  });
}
