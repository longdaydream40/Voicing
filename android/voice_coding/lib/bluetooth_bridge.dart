import 'dart:async';

import 'package:flutter/services.dart';

class BluetoothDeviceInfo {
  const BluetoothDeviceInfo({
    required this.name,
    required this.address,
  });

  final String name;
  final String address;

  factory BluetoothDeviceInfo.fromMap(Map<Object?, Object?> raw) {
    return BluetoothDeviceInfo(
      name: (raw['name'] as String?)?.trim().isNotEmpty == true
          ? raw['name'] as String
          : '未命名设备',
      address: raw['address'] as String? ?? '',
    );
  }
}

class BluetoothBridgeEvent {
  const BluetoothBridgeEvent({
    required this.type,
    this.payload,
    this.message,
    this.address,
    this.name,
  });

  final String type;
  final String? payload;
  final String? message;
  final String? address;
  final String? name;

  factory BluetoothBridgeEvent.fromMap(Map<Object?, Object?> raw) {
    return BluetoothBridgeEvent(
      type: raw['type'] as String? ?? 'unknown',
      payload: raw['payload'] as String?,
      message: raw['message'] as String?,
      address: raw['address'] as String?,
      name: raw['name'] as String?,
    );
  }
}

abstract class BluetoothBridge {
  Stream<BluetoothBridgeEvent> get events;

  Future<bool> isSupported();
  Future<bool> requestConnectPermission();
  Future<bool> requestEnableBluetooth();
  Future<void> openSystemSettings();
  Future<List<BluetoothDeviceInfo>> getBondedDevices();
  Future<void> connect({
    required String address,
    required String serviceUuid,
  });
  Future<void> disconnect();
  Future<void> send(String payload);
}

class MethodChannelBluetoothBridge implements BluetoothBridge {
  static const MethodChannel _methodChannel = MethodChannel(
    'voicing/bluetooth/methods',
  );
  static const EventChannel _eventChannel = EventChannel(
    'voicing/bluetooth/events',
  );

  @override
  Stream<BluetoothBridgeEvent> get events => _eventChannel
      .receiveBroadcastStream()
      .map((dynamic event) => BluetoothBridgeEvent.fromMap(event as Map));

  @override
  Future<void> connect({
    required String address,
    required String serviceUuid,
  }) async {
    await _methodChannel.invokeMethod<void>('connect', {
      'address': address,
      'serviceUuid': serviceUuid,
    });
  }

  @override
  Future<void> disconnect() async {
    await _methodChannel.invokeMethod<void>('disconnect');
  }

  @override
  Future<List<BluetoothDeviceInfo>> getBondedDevices() async {
    final List<dynamic>? devices = await _methodChannel.invokeListMethod<dynamic>(
      'getBondedDevices',
    );
    return (devices ?? const <dynamic>[])
        .cast<Map<Object?, Object?>>()
        .map(BluetoothDeviceInfo.fromMap)
        .toList();
  }

  @override
  Future<bool> isSupported() async {
    return (await _methodChannel.invokeMethod<bool>('isSupported')) ?? false;
  }

  @override
  Future<void> openSystemSettings() async {
    await _methodChannel.invokeMethod<void>('openSystemBluetoothSettings');
  }

  @override
  Future<bool> requestConnectPermission() async {
    return (await _methodChannel.invokeMethod<bool>(
          'requestConnectPermission',
        )) ??
        false;
  }

  @override
  Future<bool> requestEnableBluetooth() async {
    return (await _methodChannel.invokeMethod<bool>(
          'requestEnableBluetooth',
        )) ??
        false;
  }

  @override
  Future<void> send(String payload) async {
    await _methodChannel.invokeMethod<void>('send', {
      'payload': payload,
    });
  }
}
