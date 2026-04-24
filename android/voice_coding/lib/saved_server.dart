import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class SavedServer {
  static const int currentSchemaVersion = 1;

  const SavedServer({
    this.schemaVersion = currentSchemaVersion,
    required this.deviceId,
    required this.ip,
    this.ips = const [],
    required this.port,
    required this.name,
    required this.os,
    required this.lastConnectedTs,
  });

  final int schemaVersion;
  final String deviceId;
  final String ip;
  final List<String> ips;
  final int port;
  final String name;
  final String os;
  final int lastConnectedTs;

  bool get hasDeviceId => deviceId.isNotEmpty;

  String get displayName => name.isNotEmpty ? name : ip;

  List<String> get candidateIps => normalizeIpCandidates(ip, ips);

  factory SavedServer.fromJson(Map<String, dynamic> json) {
    final ip = _readString(json['ip']);
    final port = _readInt(json['port']);
    if (ip.isEmpty || port == null) {
      throw const FormatException('saved_server is missing ip or port');
    }

    return SavedServer(
      schemaVersion: _readInt(json['schema_version']) ?? currentSchemaVersion,
      deviceId: _readString(json['device_id']),
      ip: ip,
      ips: _readStringList(json['ips']),
      port: port,
      name: _readString(json['name']),
      os: _readString(json['os']),
      lastConnectedTs: _readInt(json['last_connected_ts']) ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'schema_version': schemaVersion,
      'device_id': deviceId,
      'ip': ip,
      'ips': candidateIps,
      'port': port,
      'name': name,
      'os': os,
      'last_connected_ts': lastConnectedTs,
    };
  }

  SavedServer copyWith({
    int? schemaVersion,
    String? deviceId,
    String? ip,
    List<String>? ips,
    int? port,
    String? name,
    String? os,
    int? lastConnectedTs,
  }) {
    return SavedServer(
      schemaVersion: schemaVersion ?? this.schemaVersion,
      deviceId: deviceId ?? this.deviceId,
      ip: ip ?? this.ip,
      ips: ips ?? this.ips,
      port: port ?? this.port,
      name: name ?? this.name,
      os: os ?? this.os,
      lastConnectedTs: lastConnectedTs ?? this.lastConnectedTs,
    );
  }

  static String readString(dynamic value) => _readString(value);

  static int? readInt(dynamic value) => _readInt(value);

  static List<String> normalizeIpCandidates(
    String primaryIp,
    Iterable<dynamic> values,
  ) {
    final candidates = <String>[];

    void add(dynamic value) {
      final ip = _readString(value);
      if (ip.isNotEmpty && !candidates.contains(ip)) {
        candidates.add(ip);
      }
    }

    add(primaryIp);
    for (final value in values) {
      add(value);
    }
    return candidates;
  }

  static String _readString(dynamic value) {
    return value is String ? value.trim() : '';
  }

  static List<String> _readStringList(dynamic value) {
    if (value is! List) {
      return const [];
    }
    return normalizeIpCandidates('', value);
  }

  static int? _readInt(dynamic value) {
    if (value is int) {
      return value;
    }
    if (value is num) {
      return value.toInt();
    }
    if (value is String) {
      return int.tryParse(value);
    }
    return null;
  }

  @override
  bool operator ==(Object other) {
    return other is SavedServer &&
        other.schemaVersion == schemaVersion &&
        other.deviceId == deviceId &&
        other.ip == ip &&
        _listEquals(other.candidateIps, candidateIps) &&
        other.port == port &&
        other.name == name &&
        other.os == os &&
        other.lastConnectedTs == lastConnectedTs;
  }

  @override
  int get hashCode => Object.hash(
        schemaVersion,
        deviceId,
        ip,
        Object.hashAll(candidateIps),
        port,
        name,
        os,
        lastConnectedTs,
      );
}

bool _listEquals(List<String> a, List<String> b) {
  if (identical(a, b)) {
    return true;
  }
  if (a.length != b.length) {
    return false;
  }
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) {
      return false;
    }
  }
  return true;
}

class SavedServerStore {
  static const String savedServerKey = 'saved_server';
  static const String legacyManualServerIpKey = 'manual_server_ip';
  static const String legacyManualServerPortKey = 'manual_server_port';

  const SavedServerStore();

  Future<SavedServer?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final rawSavedServer = prefs.getString(savedServerKey);
    if (rawSavedServer != null && rawSavedServer.isNotEmpty) {
      try {
        final decoded = json.decode(rawSavedServer);
        if (decoded is Map) {
          return SavedServer.fromJson(Map<String, dynamic>.from(decoded));
        }
      } catch (_) {
        await prefs.remove(savedServerKey);
      }
    }

    return _migrateLegacyManualServer(prefs);
  }

  Future<void> save(SavedServer server) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(savedServerKey, json.encode(server.toJson()));
    await prefs.remove(legacyManualServerIpKey);
    await prefs.remove(legacyManualServerPortKey);
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(savedServerKey);
    await prefs.remove(legacyManualServerIpKey);
    await prefs.remove(legacyManualServerPortKey);
  }

  Future<SavedServer?> _migrateLegacyManualServer(
    SharedPreferences prefs,
  ) async {
    final ip = prefs.getString(legacyManualServerIpKey)?.trim();
    final rawPort = prefs.get(legacyManualServerPortKey);
    final port = SavedServer.readInt(rawPort);
    if (ip == null || ip.isEmpty || port == null) {
      return null;
    }

    final migrated = SavedServer(
      deviceId: '',
      ip: ip,
      port: port,
      name: '',
      os: '',
      lastConnectedTs: DateTime.now().millisecondsSinceEpoch,
    );
    await save(migrated);
    return migrated;
  }
}
