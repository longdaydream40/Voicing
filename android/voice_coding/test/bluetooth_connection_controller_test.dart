import 'dart:async';
import 'dart:convert';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:voicing/bluetooth_bridge.dart';
import 'package:voicing/bluetooth_connection_controller.dart';
import 'package:voicing/connection_recovery_policy.dart';
import 'package:voicing/voicing_protocol.dart';

class FakeBluetoothBridge implements BluetoothBridge {
  final StreamController<BluetoothBridgeEvent> controller =
      StreamController<BluetoothBridgeEvent>.broadcast();
  final List<String> sentPayloads = [];
  final List<String> connectAddresses = [];
  bool supported = true;
  bool permissionGranted = true;
  bool enabled = true;
  List<BluetoothDeviceInfo> bondedDevices = const [
    BluetoothDeviceInfo(name: 'Voicing Desktop', address: 'AA:BB:CC:DD:EE:FF'),
  ];

  @override
  Stream<BluetoothBridgeEvent> get events => controller.stream;

  @override
  Future<void> connect({
    required String address,
    required String serviceUuid,
  }) async {
    connectAddresses.add('$address|$serviceUuid');
  }

  @override
  Future<void> disconnect() async {}

  @override
  Future<List<BluetoothDeviceInfo>> getBondedDevices() async => bondedDevices;

  @override
  Future<bool> isSupported() async => supported;

  @override
  Future<void> openSystemSettings() async {}

  @override
  Future<bool> requestConnectPermission() async => permissionGranted;

  @override
  Future<bool> requestEnableBluetooth() async => enabled;

  @override
  Future<void> send(String payload) async {
    sentPayloads.add(payload);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('initialize selects default bonded device and attempts connect', () async {
    final bridge = FakeBluetoothBridge();
    final controller = BluetoothConnectionController(
      textController: TextEditingController(),
      bridge: bridge,
    );

    await controller.initialize();

    expect(controller.bluetoothSupported, isTrue);
    expect(controller.bluetoothEnabled, isTrue);
    expect(controller.targetAddress, 'AA:BB:CC:DD:EE:FF');
    expect(bridge.connectAddresses.single, contains('AA:BB:CC:DD:EE:FF'));
  });

  test('incoming bluetooth chunks are framed and update connection state', () async {
    final bridge = FakeBluetoothBridge();
    final controller = BluetoothConnectionController(
      textController: TextEditingController(),
      bridge: bridge,
    );
    await controller.initialize();

    bridge.controller.add(
      const BluetoothBridgeEvent(
        type: 'data',
        payload: '{"type":"connected","sync_enabled":true,"message":"ok","comp',
      ),
    );
    bridge.controller.add(
      const BluetoothBridgeEvent(
        type: 'data',
        payload: 'uter_name":"DESKTOP"}\n',
      ),
    );

    await Future<void>.delayed(Duration.zero);
    expect(controller.status, ConnectionStatus.connected);
    expect(controller.syncEnabled, isTrue);
  });

  test('sendText writes JSON payload with bluetooth delimiter', () async {
    final bridge = FakeBluetoothBridge();
    final textController = TextEditingController(text: 'hello');
    final controller = BluetoothConnectionController(
      textController: textController,
      bridge: bridge,
    );
    await controller.initialize();

    bridge.controller.add(
      BluetoothBridgeEvent(
        type: 'data',
        payload:
            '${json.encode({'type': VoicingProtocol.typeConnected, 'sync_enabled': true, 'message': 'ok', 'computer_name': 'DESKTOP'})}\n',
      ),
    );
    await Future<void>.delayed(Duration.zero);

    controller.sendText();
    await Future<void>.delayed(Duration.zero);

    expect(bridge.sentPayloads, isNotEmpty);
    expect(
      bridge.sentPayloads.last.endsWith(VoicingProtocol.bluetoothMessageDelimiter),
      isTrue,
    );
    final decoded = json.decode(
      bridge.sentPayloads.last.substring(
        0,
        bridge.sentPayloads.last.length - 1,
      ),
    ) as Map<String, dynamic>;
    expect(decoded['type'], VoicingProtocol.typeText);
    expect(decoded['content'], 'hello');
  });
}
