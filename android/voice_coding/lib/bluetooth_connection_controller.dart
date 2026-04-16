import 'dart:async';
import 'dart:convert';

import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app_logger.dart';
import 'bluetooth_bridge.dart';
import 'connection_recovery_policy.dart';
import 'transport_connection_controller.dart';
import 'voicing_protocol.dart';

class BluetoothConnectionController extends ChangeNotifier
    implements TransportConnectionController {
  static const Duration _shadowFinalizeDelay = Duration(milliseconds: 700);
  static const String _autoEnterPreferenceKey = 'auto_enter_enabled';
  static const String _targetAddressPreferenceKey = 'bluetooth_target_address';

  BluetoothConnectionController({
    required this.textController,
    BluetoothBridge? bridge,
    ConnectionRecoveryPolicy recoveryPolicy = const ConnectionRecoveryPolicy(
      heartbeatTimeout: Duration(
        seconds: VoicingProtocol.heartbeatTimeoutSec,
      ),
      udpReconnectCooldown: Duration(
        milliseconds: VoicingProtocol.udpReconnectCooldownMs,
      ),
      normalConnectTimeout: Duration(
        seconds: VoicingProtocol.connectTimeoutSec,
      ),
      maxReconnectDelay: Duration(
        seconds: VoicingProtocol.maxReconnectDelaySec,
      ),
    ),
  })  : _bridge = bridge ?? MethodChannelBluetoothBridge(),
        _recoveryPolicy = recoveryPolicy {
    textController.addListener(_onTextControllerChanged);
  }

  @override
  final TextEditingController textController;
  final BluetoothBridge _bridge;
  final ConnectionRecoveryPolicy _recoveryPolicy;

  StreamSubscription<BluetoothBridgeEvent>? _eventSubscription;
  final StringBuffer _incomingBuffer = StringBuffer();
  ConnectionStatus _status = ConnectionStatus.disconnected;
  bool _syncEnabled = true;
  bool _autoEnterEnabled = false;
  bool _bluetoothSupported = false;
  bool _bluetoothEnabled = false;
  List<BluetoothDeviceInfo> _bondedDevices = const [];
  String? _targetAddress;
  String? _targetName;
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;
  Timer? _foregroundRecoveryTimer;
  Timer? _shadowFinalizeTimer;
  DateTime? _lastPong;
  DateTime? _foregroundRecoveryUntil;
  int _reconnectAttempt = 0;
  String _lastSentText = '';
  int _lastSentLength = 0;
  bool _wasComposing = false;
  bool _displayConnectedDuringForegroundRecovery = false;

  @override
  ConnectionStatus get status => _status;

  @override
  ConnectionStatus get displayStatus => _displayConnectedDuringForegroundRecovery
      ? ConnectionStatus.connected
      : _status;

  @override
  bool get syncEnabled => _syncEnabled;

  @override
  bool get autoEnterEnabled => _autoEnterEnabled;

  bool get bluetoothSupported => _bluetoothSupported;
  bool get bluetoothEnabled => _bluetoothEnabled;
  List<BluetoothDeviceInfo> get bondedDevices => _bondedDevices;
  String? get targetAddress => _targetAddress;
  String? get targetName => _targetName;

  @override
  String get lastSentText => _lastSentText;

  @override
  TransportMode get transportMode => TransportMode.bluetooth;

  @override
  Future<void> initialize() async {
    await _loadAutoEnterPreference();
    await _loadTargetAddressPreference();
    _subscribeToBridgeEvents();
    await _refreshBluetoothState(shouldConnect: true);
  }

  @override
  Future<void> handleLifecycleState(AppLifecycleState state) async {
    if (state == AppLifecycleState.paused) {
      _stopHeartbeat();
      return;
    }

    if (state == AppLifecycleState.resumed &&
        _recoveryPolicy.shouldForceReconnectOnResume()) {
      _beginForegroundRecovery();
      await _refreshBluetoothState(shouldConnect: true);
    }
  }

  @override
  void refreshConnection() {
    unawaited(_refreshBluetoothState(shouldConnect: true, forceReconnect: true));
  }

  @override
  void recallLastText() {
    if (_lastSentText.isEmpty) {
      return;
    }

    textController.text = _lastSentText;
    textController.selection = TextSelection.fromPosition(
      TextPosition(offset: _lastSentText.length),
    );
  }

  @override
  void sendText() {
    final text = textController.text.trim();
    if (text.isEmpty || _status != ConnectionStatus.connected || !_syncEnabled) {
      return;
    }

    if (_hasPendingShadowBuffer(text)) {
      _finalizeShadowInput(forceEnter: _autoEnterEnabled);
      return;
    }

    _shadowFinalizeTimer?.cancel();
    _sendProtocolMessage(
      VoicingProtocol.buildTextMessage(
        text,
        autoEnter: _autoEnterEnabled,
        sendMode: VoicingProtocol.textSendModeSubmit,
      ),
    );
    _lastSentText = text;
    _lastSentLength = 0;
  }

  Future<void> selectTargetDevice(BluetoothDeviceInfo device) async {
    _targetAddress = device.address;
    _targetName = device.name;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_targetAddressPreferenceKey, device.address);
    } catch (error, stackTrace) {
      AppLogger.warning(
        '保存蓝牙目标设备失败',
        error: error,
        stackTrace: stackTrace,
      );
    }

    unawaited(_connect(resetBackoff: true));
  }

  Future<void> openSystemBluetoothSettings() async {
    await _bridge.openSystemSettings();
  }

  Future<void> reloadBondedDevices() async {
    await _loadBondedDevices();
  }

  @override
  void dispose() {
    _eventSubscription?.cancel();
    _heartbeatTimer?.cancel();
    _reconnectTimer?.cancel();
    _foregroundRecoveryTimer?.cancel();
    _shadowFinalizeTimer?.cancel();
    textController.removeListener(_onTextControllerChanged);
    unawaited(_bridge.disconnect());
    super.dispose();
  }

  @override
  Future<void> toggleAutoEnter() async {
    _autoEnterEnabled = !_autoEnterEnabled;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_autoEnterPreferenceKey, _autoEnterEnabled);
      AppLogger.info('保存自动 Enter 设置: $_autoEnterEnabled');
    } catch (error, stackTrace) {
      AppLogger.warning('保存自动 Enter 设置失败', error: error, stackTrace: stackTrace);
    }
  }

  void _subscribeToBridgeEvents() {
    _eventSubscription ??= _bridge.events.listen(
      _handleBridgeEvent,
      onError: (Object error, StackTrace stackTrace) {
        AppLogger.warning('蓝牙事件流异常', error: error, stackTrace: stackTrace);
      },
    );
  }

  Future<void> _refreshBluetoothState({
    required bool shouldConnect,
    bool forceReconnect = false,
  }) async {
    _bluetoothSupported = await _bridge.isSupported();
    if (!_bluetoothSupported) {
      _status = ConnectionStatus.disconnected;
      notifyListeners();
      return;
    }

    final bool permissionGranted = await _bridge.requestConnectPermission();
    if (!permissionGranted) {
      _status = ConnectionStatus.disconnected;
      notifyListeners();
      return;
    }

    _bluetoothEnabled = await _bridge.requestEnableBluetooth();
    if (!_bluetoothEnabled) {
      _status = ConnectionStatus.disconnected;
      notifyListeners();
      return;
    }

    await _loadBondedDevices();
    _selectDefaultDeviceIfNeeded();
    notifyListeners();

    if (shouldConnect && _targetAddress != null) {
      await _connect(resetBackoff: forceReconnect);
    }
  }

  Future<void> _connect({bool resetBackoff = false}) async {
    final targetAddress = _targetAddress;
    if (targetAddress == null || !_bluetoothEnabled) {
      return;
    }

    if (resetBackoff) {
      _reconnectAttempt = 0;
    }

    _reconnectTimer?.cancel();
    _stopHeartbeat();
    _lastPong = null;
    _setStatus(ConnectionStatus.connecting);
    _incomingBuffer.clear();

    try {
      await _bridge.disconnect();
    } catch (_) {}

    try {
      await _bridge.connect(
        address: targetAddress,
        serviceUuid: VoicingProtocol.bluetoothServiceUuid,
      );
    } catch (error, stackTrace) {
      AppLogger.warning('蓝牙连接失败', error: error, stackTrace: stackTrace);
      _handleDisconnect();
    }
  }

  void _handleBridgeEvent(BluetoothBridgeEvent event) {
    switch (event.type) {
      case 'connected':
        _targetAddress = event.address ?? _targetAddress;
        _targetName = event.name ?? _targetName;
        notifyListeners();
        return;
      case 'data':
        _handleIncomingChunk(event.payload ?? '');
        return;
      case 'disconnected':
        _handleDisconnect();
        return;
      case 'error':
        AppLogger.warning('蓝牙错误: ${event.message ?? 'unknown'}');
        _handleDisconnect();
        return;
    }
  }

  void _handleIncomingChunk(String chunk) {
    _incomingBuffer.write(chunk);
    final payload = _incomingBuffer.toString();
    final segments = payload.split(VoicingProtocol.bluetoothMessageDelimiter);
    _incomingBuffer
      ..clear()
      ..write(segments.removeLast());

    for (final segment in segments) {
      if (segment.trim().isEmpty) {
        continue;
      }
      _handleMessage(segment);
    }
  }

  void _handleMessage(String message) {
    try {
      final data = VoicingProtocol.decodeMessage(message);
      if (data == null) {
        return;
      }

      final type = data['type'];
      if (type == VoicingProtocol.typeConnected) {
        _endForegroundRecovery();
        _status = ConnectionStatus.connected;
        _syncEnabled = data['sync_enabled'] ?? true;
        _reconnectAttempt = 0;
        _lastPong = DateTime.now();
        _startHeartbeat();
        notifyListeners();
      } else if (type == VoicingProtocol.typeAck) {
        final shouldClearInput = data['clear_input'];
        if (shouldClearInput is bool ? shouldClearInput : true) {
          textController.clear();
        }
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
        '蓝牙消息解析失败',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  void _handleDisconnect() {
    final now = DateTime.now();
    final foregroundRecoveryActive = _isForegroundRecoveryActive(now: now);
    _stopHeartbeat();
    _status = foregroundRecoveryActive
        ? ConnectionStatus.connecting
        : ConnectionStatus.disconnected;
    _syncEnabled = true;
    notifyListeners();

    if (_targetAddress == null || !_bluetoothEnabled) {
      return;
    }

    final reconnectDelay = _recoveryPolicy.reconnectDelay(
      reconnectAttempt: _reconnectAttempt,
      foregroundRecoveryActive: foregroundRecoveryActive,
    );
    _reconnectAttempt = foregroundRecoveryActive ? 0 : _reconnectAttempt + 1;

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(reconnectDelay, () {
      if (_status == ConnectionStatus.disconnected ||
          _status == ConnectionStatus.connecting) {
        unawaited(_connect());
      }
    });
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
      AppLogger.warning('蓝牙心跳超时，判定连接死亡');
      _handleDisconnect();
      return;
    }

    _sendProtocolMessage(VoicingProtocol.buildPingMessage());
  }

  void _sendProtocolMessage(Map<String, dynamic> message) {
    final payload = '${json.encode(message)}${VoicingProtocol.bluetoothMessageDelimiter}';
    unawaited(_bridge.send(payload).catchError((Object error, StackTrace stackTrace) {
      AppLogger.warning('蓝牙发送失败', error: error, stackTrace: stackTrace);
      _handleDisconnect();
    }));
  }

  Future<void> _loadBondedDevices() async {
    try {
      _bondedDevices = await _bridge.getBondedDevices();
    } catch (error, stackTrace) {
      AppLogger.warning('读取已配对蓝牙设备失败', error: error, stackTrace: stackTrace);
      _bondedDevices = const [];
    }
  }

  void _selectDefaultDeviceIfNeeded() {
    if (_targetAddress != null &&
        _bondedDevices.any((device) => device.address == _targetAddress)) {
      final device = _bondedDevices.firstWhere(
        (entry) => entry.address == _targetAddress,
      );
      _targetName = device.name;
      return;
    }

    final matchingDevice = _bondedDevices.cast<BluetoothDeviceInfo?>().firstWhere(
          (device) => (device?.name.toLowerCase().contains('voicing') ?? false),
          orElse: () => _bondedDevices.isNotEmpty ? _bondedDevices.first : null,
        );
    if (matchingDevice != null) {
      _targetAddress = matchingDevice.address;
      _targetName = matchingDevice.name;
    }
  }

  void _beginForegroundRecovery() {
    final now = DateTime.now();
    _foregroundRecoveryUntil = _recoveryPolicy.startForegroundRecovery(now);
    _displayConnectedDuringForegroundRecovery =
        _status == ConnectionStatus.connected;
    _foregroundRecoveryTimer?.cancel();
    _foregroundRecoveryTimer = Timer(
      _foregroundRecoveryUntil!.difference(now),
      () {
        if (_displayConnectedDuringForegroundRecovery) {
          _displayConnectedDuringForegroundRecovery = false;
          notifyListeners();
        }
      },
    );
    notifyListeners();
  }

  void _endForegroundRecovery() {
    _foregroundRecoveryUntil = null;
    _foregroundRecoveryTimer?.cancel();
    _foregroundRecoveryTimer = null;
    _displayConnectedDuringForegroundRecovery = false;
  }

  bool _isForegroundRecoveryActive({DateTime? now}) {
    final currentTime = now ?? DateTime.now();
    final active = _recoveryPolicy.isForegroundRecoveryActive(
      recoveryUntil: _foregroundRecoveryUntil,
      now: currentTime,
    );
    if (!active) {
      _foregroundRecoveryUntil = null;
    }
    return active;
  }

  void _onTextControllerChanged() {
    final currentText = textController.text;

    if (currentText.length < _lastSentLength) {
      _lastSentLength = currentText.length;
    }

    if (_status != ConnectionStatus.connected || !_syncEnabled) {
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
    _sendProtocolMessage(
      VoicingProtocol.buildTextMessage(
        increment,
        autoEnter: false,
        sendMode: VoicingProtocol.textSendModeShadow,
      ),
    );
    _lastSentLength = currentText.length;
    _lastSentText = currentText;
    _scheduleShadowFinalize();
  }

  bool _hasPendingShadowBuffer(String text) {
    return _lastSentLength > 0 &&
        _lastSentLength == text.length &&
        _lastSentText == text;
  }

  void _scheduleShadowFinalize() {
    _shadowFinalizeTimer?.cancel();
    _shadowFinalizeTimer = Timer(
      _shadowFinalizeDelay,
      () => _finalizeShadowInput(forceEnter: _autoEnterEnabled),
    );
  }

  void _finalizeShadowInput({required bool forceEnter}) {
    _shadowFinalizeTimer?.cancel();
    _shadowFinalizeTimer = null;

    final currentText = textController.text.trim();
    if (!_hasPendingShadowBuffer(currentText)) {
      return;
    }

    if (forceEnter &&
        _status == ConnectionStatus.connected &&
        _syncEnabled) {
      _sendProtocolMessage(
        VoicingProtocol.buildTextMessage(
          '',
          autoEnter: true,
          sendMode: VoicingProtocol.textSendModeCommit,
        ),
      );
    }

    _lastSentLength = 0;
    _wasComposing = false;
    textController.clear();
  }

  Future<void> _loadAutoEnterPreference() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _autoEnterEnabled = prefs.getBool(_autoEnterPreferenceKey) ?? false;
    } catch (error, stackTrace) {
      AppLogger.warning('加载自动 Enter 设置失败', error: error, stackTrace: stackTrace);
    }
  }

  Future<void> _loadTargetAddressPreference() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _targetAddress = prefs.getString(_targetAddressPreferenceKey);
    } catch (error, stackTrace) {
      AppLogger.warning('加载蓝牙目标设备失败', error: error, stackTrace: stackTrace);
    }
  }

  void _setStatus(ConnectionStatus status) {
    _status = status;
    notifyListeners();
  }
}
