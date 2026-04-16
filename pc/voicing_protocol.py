DEFAULT_SERVER_IP = "192.168.137.1"
WEBSOCKET_PORT = 9527
UDP_BROADCAST_PORT = 9530
BLUETOOTH_RFCOMM_CHANNEL = 11
BLUETOOTH_SERVICE_UUID = "8b3e3f4b-6f8f-4f2f-9d5d-77f4f84f9d11"
BLUETOOTH_MESSAGE_DELIMITER = "\n"

UDP_DISCOVERY_TYPE = "voice_coding_server"

TYPE_TEXT = "text"
TYPE_PING = "ping"
TYPE_CONNECTED = "connected"
TYPE_ACK = "ack"
TYPE_PONG = "pong"
TYPE_SYNC_STATE = "sync_state"
TYPE_SYNC_DISABLED = "sync_disabled"
TEXT_SEND_MODE_SUBMIT = "submit"
TEXT_SEND_MODE_SHADOW = "shadow"
TEXT_SEND_MODE_COMMIT = "commit"

CLIENT_TO_SERVER_TYPES = {
    TYPE_TEXT,
    TYPE_PING,
}

SERVER_TO_CLIENT_TYPES = {
    TYPE_CONNECTED,
    TYPE_ACK,
    TYPE_PONG,
    TYPE_SYNC_STATE,
    TYPE_SYNC_DISABLED,
}


def build_connected_message(sync_enabled: bool, computer_name: str) -> dict:
    return {
        "type": TYPE_CONNECTED,
        "message": "Connected to Voicing server",
        "sync_enabled": sync_enabled,
        "computer_name": computer_name,
    }


def build_ack_message(clear_input: bool = True) -> dict:
    return {
        "type": TYPE_ACK,
        "message": "Text received and typed",
        "clear_input": clear_input,
    }


def build_pong_message(sync_enabled: bool) -> dict:
    return {
        "type": TYPE_PONG,
        "sync_enabled": sync_enabled,
    }


def build_sync_state_message(sync_enabled: bool) -> dict:
    return {
        "type": TYPE_SYNC_STATE,
        "sync_enabled": sync_enabled,
    }


def build_sync_disabled_message() -> dict:
    return {
        "type": TYPE_SYNC_DISABLED,
        "sync_enabled": False,
        "message": "Sync is disabled on PC",
    }


def build_text_message(
    content: str,
    auto_enter: bool = False,
    send_mode: str = TEXT_SEND_MODE_SUBMIT,
) -> dict:
    return {
        "type": TYPE_TEXT,
        "content": content,
        "auto_enter": auto_enter,
        "send_mode": send_mode,
    }


def build_ping_message() -> dict:
    return {
        "type": TYPE_PING,
    }
