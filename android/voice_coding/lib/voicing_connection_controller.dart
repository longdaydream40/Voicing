import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'app_logger.dart';
import 'connection_recovery_policy.dart';
import 'voicing_protocol.dart';

class VoicingConnectionController extends ChangeNotifier {
  VoicingConnectionController({
    ConnectionRecoveryPolicy recoveryPolicy = const ConnectionRecoveryPolicy(
      heartbeatTimeout: Duration(
        seconds: VoicingProtocol.heartbeatTimeoutSec,
      ),
      udpReconnectCooldown: Duration(
        milliseconds: VoicingProtocol.udpReconnectCooldownMs,
      ),
    ),
  }) : _recoveryPolicy = recoveryPolicy {
    textController.addListener(_onTextControllerChanged);
  }

  final TextEditingController textController = TextEditingController();
  final ConnectionRecoveryPolicy _recoveryPolicy;

  WebSocketChannel? _channel;
  ConnectionStatus _status = ConnectionStatus.disconnected;
  bool _syncEnabled = true;
  Timer? _reconnectTimer;
  String _serverIp = VoicingProtocol.defaultServerIp;
  int _serverPort = VoicingProtocol.websocketPort;
  String _lastSentText = '';
  bool _shadowModeEnabled = false;
  int _lastSentLength = 0;
  bool _wasComposing = false;
  RawDatagramSocket? _udpSocket;
  StreamSubscription<RawSocketEvent>? _udpSubscription;
  Timer? _heartbeatTimer;
  DateTime? _lastPong;
  int _reconnectAttempt = 0;
  int _connectionGeneration = 0;
  DateTime? _lastConnectStartedAt;

  ConnectionStatus get status => _status;
  bool get syncEnabled => _syncEnabled;
  String get serverIp => _serverIp;
  int get serverPort => _serverPort;
  String get lastSentText => _lastSentText;
  bool get shadowModeEnabled => _shadowModeEnabled;

  Future<void> initialize() async {
    await _loadPreferences();
    await _startUdpDiscovery();
    _forceReconnect(resetBackoff: true, reason: 'init');
  }

  Future<void> handleLifecycleState(AppLifecycleState state) async {
    if (state == AppLifecycleState.paused) {
      _stopHeartbeat();
    } else if (state == AppLifecycleState.resumed &&
        _recoveryPolicy.shouldForceReconnectOnResume()) {
      _forceReconnect(resetBackoff: true, reason: 'app resumed');
    }
  }

  Future<void> setShadowModeEnabled(bool value) async {
    _shadowModeEnabled = value;
    if (value) {
      _lastSentLength = textController.text.length;
      _wasComposing = false;
    } else {
      _lastSentLength = 0;
      _wasComposing = false;
    }
    notifyListeners();
    await _saveAutoSendPreference(value);
  }

  void refreshConnection() {
    _forceReconnect(resetBackoff: true, reason: 'manual refresh');
  }

  void recallLastText() {
    if (_lastSentText.isEmpty) {
      return;
    }

    textController.text = _lastSentText;
    textController.selection = TextSelection.fromPosition(
      TextPosition(offset: _lastSentText.length),
    );
  }

  void sendText() {
    final text = textController.text.trim();
    if (text.isEmpty || _status != ConnectionStatus.connected || !_syncEnabled) {
      return;
    }

    try {
      _channel?.sink.add(json.encode(VoicingProtocol.buildTextMessage(text)));
      _lastSentText = text;
      _lastSentLength = 0;
    } catch (error, stackTrace) {
      AppLogger.error('发送失败', error: error, stackTrace: stackTrace);
      _handleDisconnect();
    }
  }

  @override
  void dispose() {
    _reconnectTimer?.cancel();
    _heartbeatTimer?.cancel();
    textController.removeListener(_onTextControllerChanged);
    _connectionGeneration++;
    _channel?.sink.close();
    textController.dispose();
    _udpSubscription?.cancel();
    _udpSocket?.close();
    super.dispose();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    _shadowModeEnabled = prefs.getBool('autoSendEnabled') ?? false;
    notifyListeners();
  }

  Future<void> _saveAutoSendPreference(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('autoSendEnabled', value);
  }

  void _forceReconnect({
    bool resetBackoff = false,
    String reason = '',
  }) {
    if (resetBackoff) {
      _reconnectAttempt = 0;
    }

    if (reason.isNotEmpty) {
      AppLogger.info('开始重连: $reason');
    }

    _connect();
  }

  void _connect() {
    final int connectionId = ++_connectionGeneration;
    _lastConnectStartedAt = DateTime.now();
    _setStatus(ConnectionStatus.connecting);

    _reconnectTimer?.cancel();
    _stopHeartbeat();
    _channel?.sink.close();
    _lastPong = null;

    try {
      _channel = IOWebSocketChannel.connect(
        Uri.parse('ws://$_serverIp:$_serverPort'),
        connectTimeout: const Duration(
          seconds: VoicingProtocol.connectTimeoutSec,
        ),
      );

      _channel!.stream.listen(
        (message) => _handleMessage(message, connectionId),
        onError: (error, stackTrace) {
          if (connectionId != _connectionGeneration) {
            return;
          }
          AppLogger.warning(
            'WebSocket error',
            error: error,
            stackTrace: stackTrace,
          );
          _handleDisconnect(connectionId: connectionId);
        },
        onDone: () {
          if (connectionId != _connectionGeneration) {
            return;
          }
          _handleDisconnect(connectionId: connectionId);
        },
      );
    } catch (error, stackTrace) {
      if (connectionId != _connectionGeneration) {
        return;
      }
      AppLogger.error('Connection error', error: error, stackTrace: stackTrace);
      _handleDisconnect(connectionId: connectionId);
    }
  }

  void _handleMessage(dynamic message, int connectionId) {
    if (connectionId != _connectionGeneration) {
      return;
    }

    try {
      final data = VoicingProtocol.decodeMessage(message);
      if (data == null) {
        return;
      }

      final type = data['type'];
      if (type == VoicingProtocol.typeConnected) {
        _status = ConnectionStatus.connected;
        _syncEnabled = data['sync_enabled'] ?? true;
        _reconnectAttempt = 0;
        _lastPong = DateTime.now();
        _startHeartbeat();
        notifyListeners();
      } else if (type == VoicingProtocol.typeAck) {
        textController.clear();
      } else if (type == VoicingProtocol.typeSyncDisabled) {
        _lastPong = DateTime.now();
        _syncEnabled = data['sync_enabled'] ?? false;
        notifyListeners();
      } else if (type == VoicingProtocol.typeSyncState ||
          type == VoicingProtocol.typePong) {
        _lastPong = DateTime.now();
        _syncEnabled = data['sync_enabled'] ?? true;
        notifyListeners();
      }
    } catch (error, stackTrace) {
      AppLogger.warning(
        'Message parse error',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  void _handleDisconnect({int? connectionId}) {
    if (connectionId != null && connectionId != _connectionGeneration) {
      return;
    }

    _stopHeartbeat();
    if (_status == ConnectionStatus.disconnected) {
      return;
    }

    _status = ConnectionStatus.disconnected;
    _syncEnabled = true;
    notifyListeners();

    final delaySec = (_reconnectAttempt < 5)
        ? 3 * (1 << _reconnectAttempt)
        : VoicingProtocol.maxReconnectDelaySec;
    _reconnectAttempt++;

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(
      Duration(
        seconds: delaySec.clamp(3, VoicingProtocol.maxReconnectDelaySec),
      ),
      () {
        if (_status == ConnectionStatus.disconnected) {
          _connect();
        }
      },
    );
  }

  void _startHeartbeat() {
    _stopHeartbeat();
    _heartbeatTimer = Timer.periodic(
      const Duration(seconds: VoicingProtocol.heartbeatIntervalSec),
      (_) => _checkHeartbeat(),
    );
  }

  void _stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  void _checkHeartbeat() {
    if (_status != ConnectionStatus.connected) {
      _stopHeartbeat();
      return;
    }

    final now = DateTime.now();
    if (_recoveryPolicy.isHeartbeatExpired(
      status: _status,
      lastPong: _lastPong,
      now: now,
    )) {
      final elapsed = _lastPong == null ? 0 : now.difference(_lastPong!).inSeconds;
      AppLogger.warning('心跳超时 (${elapsed}s)，判定连接死亡');
      _handleDisconnect();
      return;
    }

    _sendPing();
  }

  void _sendPing() {
    try {
      _channel?.sink.add(json.encode(VoicingProtocol.buildPingMessage()));
    } catch (error, stackTrace) {
      AppLogger.warning('Ping 发送失败', error: error, stackTrace: stackTrace);
      _handleDisconnect();
    }
  }

  Future<void> _startUdpDiscovery() async {
    try {
      _udpSocket = await RawDatagramSocket.bind(
        InternetAddress.anyIPv4,
        VoicingProtocol.udpBroadcastPort,
      );
      _udpSocket!.broadcastEnabled = true;
      _udpSocket!.multicastLoopback = true;
      AppLogger.info('UDP 发现监听已启动，端口: ${VoicingProtocol.udpBroadcastPort}');

      _udpSubscription = _udpSocket!.listen((RawSocketEvent event) {
        if (event != RawSocketEvent.read) {
          return;
        }

        final datagram = _udpSocket!.receive();
        if (datagram == null) {
          return;
        }

        final message = utf8.decode(datagram.data);
        _handleUdpDiscovery(message, datagram.address.address);
      });
    } catch (error, stackTrace) {
      AppLogger.warning(
        'UDP 发现启动失败',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  void _handleUdpDiscovery(String message, String sourceIp) {
    try {
      final announcement = VoicingProtocol.parseUdpDiscoveryMessage(message);
      if (announcement == null) {
        return;
      }

      final bool serverChanged = _serverIp != announcement.ip ||
          _serverPort != announcement.port;
      final bool shouldReconnectFromBroadcast = _recoveryPolicy.shouldReconnectFromUdp(
        serverChanged: serverChanged,
        status: _status,
        lastConnectStartedAt: _lastConnectStartedAt,
        now: DateTime.now(),
      );

      if (serverChanged) {
        AppLogger.info(
          'UDP 发现服务器: ${announcement.ip}:${announcement.port} (来源: $sourceIp)',
        );
        _serverIp = announcement.ip;
        _serverPort = announcement.port;
        notifyListeners();
      }

      if (shouldReconnectFromBroadcast) {
        _reconnectTimer?.cancel();
        _forceReconnect(
          resetBackoff: true,
          reason: serverChanged ? 'udp server update' : 'udp recovery probe',
        );
      }
    } catch (error, stackTrace) {
      AppLogger.warning(
        'UDP 消息解析失败',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  void _onTextControllerChanged() {
    final currentText = textController.text;

    if (currentText.length < _lastSentLength) {
      _lastSentLength = currentText.length;
    }

    if (!_shadowModeEnabled ||
        _status != ConnectionStatus.connected ||
        !_syncEnabled) {
      return;
    }

    final composing = textController.value.composing;
    final isComposing = composing.isValid && !composing.isCollapsed;
    if (_wasComposing && !isComposing) {
      _sendShadowIncrement(currentText);
    }

    _wasComposing = isComposing;
  }

  void _sendShadowIncrement(String currentText) {
    if (currentText.length <= _lastSentLength) {
      return;
    }

    final increment = currentText.substring(_lastSentLength);
    try {
      _channel?.sink.add(json.encode(VoicingProtocol.buildTextMessage(increment)));
      _lastSentLength = currentText.length;
      _lastSentText = currentText;
    } catch (error, stackTrace) {
      AppLogger.warning('自动发送失败', error: error, stackTrace: stackTrace);
    }
  }

  void _setStatus(ConnectionStatus status) {
    _status = status;
    notifyListeners();
  }
}
