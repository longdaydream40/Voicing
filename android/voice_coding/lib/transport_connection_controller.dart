import 'package:flutter/widgets.dart';

import 'connection_recovery_policy.dart';

enum TransportMode {
  wifi,
  bluetooth,
}

abstract class TransportConnectionController implements Listenable {
  TextEditingController get textController;
  ConnectionStatus get status;
  ConnectionStatus get displayStatus;
  bool get syncEnabled;
  bool get autoEnterEnabled;
  String get lastSentText;
  TransportMode get transportMode;

  Future<void> initialize();
  Future<void> handleLifecycleState(AppLifecycleState state);
  void refreshConnection();
  void recallLastText();
  void sendText();
  Future<void> toggleAutoEnter();
  void dispose();
}
