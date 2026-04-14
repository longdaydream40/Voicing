import 'dart:convert';

class VoicingProtocol {
  static const String defaultServerIp = '192.168.137.1';
  static const int websocketPort = 9527;
  static const int udpBroadcastPort = 9530;
  static const int heartbeatIntervalSec = 15;
  static const int heartbeatTimeoutSec = 30;
  static const int connectTimeoutSec = 8;
  static const int maxReconnectDelaySec = 30;
  static const int udpReconnectCooldownMs = 3000;

  static const String udpDiscoveryType = 'voice_coding_server';

  static const String typeText = 'text';
  static const String typePing = 'ping';
  static const String typeConnected = 'connected';
  static const String typeAck = 'ack';
  static const String typePong = 'pong';
  static const String typeSyncState = 'sync_state';
  static const String typeSyncDisabled = 'sync_disabled';

  static const Set<String> clientMessageTypes = {
    typeText,
    typePing,
  };

  static const Set<String> serverMessageTypes = {
    typeConnected,
    typeAck,
    typePong,
    typeSyncState,
    typeSyncDisabled,
  };

  static Map<String, dynamic> buildTextMessage(String content) {
    return {
      'type': typeText,
      'content': content,
    };
  }

  static Map<String, dynamic> buildPingMessage() {
    return {'type': typePing};
  }

  static Map<String, dynamic>? decodeMessage(dynamic message) {
    if (message is! String) {
      return null;
    }

    final decoded = json.decode(message);
    return decoded is Map<String, dynamic> ? decoded : null;
  }

  static UdpDiscoveryAnnouncement? parseUdpDiscoveryMessage(String message) {
    final decoded = json.decode(message);
    if (decoded is! Map<String, dynamic>) {
      return null;
    }

    if (decoded['type'] != udpDiscoveryType) {
      return null;
    }

    final ip = decoded['ip'];
    final port = decoded['port'];
    final name = decoded['name'];
    if (ip is! String || port is! int || name is! String) {
      return null;
    }

    return UdpDiscoveryAnnouncement(ip: ip, port: port, name: name);
  }
}

class UdpDiscoveryAnnouncement {
  const UdpDiscoveryAnnouncement({
    required this.ip,
    required this.port,
    required this.name,
  });

  final String ip;
  final int port;
  final String name;
}
