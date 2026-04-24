import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:voicing/saved_server.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('saved server serializes expected json shape', () {
    const server = SavedServer(
      deviceId: 'abc123',
      ip: '192.168.1.23',
      port: 9527,
      name: 'Kevin-Desktop',
      os: 'windows',
      lastConnectedTs: 1713883200000,
    );

    expect(server.toJson(), {
      'schema_version': 1,
      'device_id': 'abc123',
      'ip': '192.168.1.23',
      'ips': ['192.168.1.23'],
      'port': 9527,
      'name': 'Kevin-Desktop',
      'os': 'windows',
      'last_connected_ts': 1713883200000,
    });
    expect(SavedServer.fromJson(server.toJson()), server);
  });

  test('saved server keeps primary ip first and de-duplicates candidates', () {
    const server = SavedServer(
      deviceId: 'abc123',
      ip: '10.16.177.83',
      ips: ['192.168.137.1', '10.16.177.83', '192.168.137.1'],
      port: 9527,
      name: 'Kevin-Desktop',
      os: 'windows',
      lastConnectedTs: 1713883200000,
    );

    expect(server.candidateIps, ['10.16.177.83', '192.168.137.1']);
    expect(server.toJson()['ips'], ['10.16.177.83', '192.168.137.1']);
  });

  test('saved server promotes connected ip without losing older candidates',
      () {
    const server = SavedServer(
      deviceId: 'abc123',
      ip: '192.168.137.1',
      ips: ['192.168.137.1', '10.16.177.83'],
      port: 9527,
      name: 'Kevin-Desktop',
      os: 'windows',
      lastConnectedTs: 1713883200000,
    );

    final updated = server.copyWith(
      ip: '10.16.177.83',
      ips: server.candidateIps,
    );

    expect(updated.candidateIps, ['10.16.177.83', '192.168.137.1']);
    expect(updated.toJson()['ips'], ['10.16.177.83', '192.168.137.1']);
  });

  test('saved server loads legacy single-ip blobs as one candidate', () {
    final server = SavedServer.fromJson({
      'schema_version': 1,
      'device_id': 'abc123',
      'ip': '192.168.137.1',
      'port': 9527,
      'name': 'Kevin-Desktop',
      'os': 'windows',
      'last_connected_ts': 1713883200000,
    });

    expect(server.ip, '192.168.137.1');
    expect(server.candidateIps, ['192.168.137.1']);
  });

  test('store saves and loads saved_server blob', () async {
    const store = SavedServerStore();
    const server = SavedServer(
      deviceId: 'abc123',
      ip: '192.168.1.23',
      port: 9527,
      name: 'Kevin-Desktop',
      os: 'windows',
      lastConnectedTs: 1713883200000,
    );

    await store.save(server);

    final loaded = await store.load();
    expect(loaded, server);
  });

  test('store migrates legacy manual ip keys to saved_server', () async {
    SharedPreferences.setMockInitialValues({
      SavedServerStore.legacyManualServerIpKey: '10.0.0.8',
      SavedServerStore.legacyManualServerPortKey: 9527,
    });

    const store = SavedServerStore();
    final migrated = await store.load();

    expect(migrated, isNotNull);
    expect(migrated!.deviceId, '');
    expect(migrated.ip, '10.0.0.8');
    expect(migrated.port, 9527);

    final prefs = await SharedPreferences.getInstance();
    expect(
        prefs.containsKey(SavedServerStore.legacyManualServerIpKey), isFalse);
    expect(
      prefs.containsKey(SavedServerStore.legacyManualServerPortKey),
      isFalse,
    );

    final rawSavedServer = prefs.getString(SavedServerStore.savedServerKey);
    expect(rawSavedServer, isNotNull);
    final savedJson = json.decode(rawSavedServer!) as Map<String, dynamic>;
    expect(savedJson['ip'], '10.0.0.8');
    expect(savedJson['ips'], ['10.0.0.8']);
    expect(savedJson['port'], 9527);
  });
}
