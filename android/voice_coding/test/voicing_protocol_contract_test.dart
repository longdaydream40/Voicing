import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:voicing/voicing_protocol.dart';

Map<String, dynamic> loadContract() {
  final contractPath = File(
    '${Directory.current.path}${Platform.pathSeparator}..${Platform.pathSeparator}..${Platform.pathSeparator}protocol${Platform.pathSeparator}voicing_protocol_contract.json',
  );
  return json.decode(contractPath.readAsStringSync()) as Map<String, dynamic>;
}

void main() {
  final contract = loadContract();

  test('ports match contract', () {
    final ports = contract['ports'] as Map<String, dynamic>;
    expect(VoicingProtocol.websocketPort, ports['websocket']);
    expect(VoicingProtocol.udpBroadcastPort, ports['udp_broadcast']);
    expect(VoicingProtocol.defaultServerIp, '192.168.137.1');
  });

  test('udp discovery type matches contract', () {
    final udpDiscovery = contract['udp_discovery'] as Map<String, dynamic>;
    expect(VoicingProtocol.udpDiscoveryType, udpDiscovery['type']);
  });

  test('client message builders match contract', () {
    final messages = contract['messages'] as Map<String, dynamic>;
    final clientMessages = messages['client_to_server'] as Map<String, dynamic>;

    expect(
      VoicingProtocol.clientMessageTypes,
      equals(clientMessages.keys.toSet()),
    );
    expect(
      VoicingProtocol.buildTextMessage('hello').keys.toSet(),
      equals((clientMessages['text'] as List<dynamic>).cast<String>().toSet()),
    );
    expect(
      VoicingProtocol.buildTextMessage('hello')['send_mode'],
      VoicingProtocol.textSendModeSubmit,
    );
    expect(
      VoicingProtocol.buildTextMessage(
        'hello',
        sendMode: VoicingProtocol.textSendModeShadow,
      )['send_mode'],
      VoicingProtocol.textSendModeShadow,
    );
    expect(
      VoicingProtocol.buildPingMessage().keys.toSet(),
      equals((clientMessages['ping'] as List<dynamic>).cast<String>().toSet()),
    );
    expect(
      VoicingProtocol.buildQrScanProbeMessage(),
      {
        'type': VoicingProtocol.typePing,
        'source': VoicingProtocol.qrScanPingSource
      },
    );
  });

  test('server message types match contract', () {
    final messages = contract['messages'] as Map<String, dynamic>;
    final serverMessages = messages['server_to_client'] as Map<String, dynamic>;

    expect(
      VoicingProtocol.serverMessageTypes,
      equals(serverMessages.keys.toSet()),
    );
  });

  test('udp discovery parser accepts shared contract shape', () {
    final parsed = VoicingProtocol.parseUdpDiscoveryMessage(
      json.encode({
        'type': VoicingProtocol.udpDiscoveryType,
        'ip': '192.168.137.1',
        'port': VoicingProtocol.websocketPort,
        'name': 'DESKTOP',
        'device_id': 'abc123',
        'os': 'windows',
      }),
    );

    expect(parsed, isNotNull);
    expect(parsed!.ip, '192.168.137.1');
    expect(parsed.port, VoicingProtocol.websocketPort);
    expect(parsed.name, 'DESKTOP');
    expect(parsed.deviceId, 'abc123');
    expect(parsed.os, 'windows');
  });
}
