DEFAULT_SERVER_IP = "192.168.137.1"
WEBSOCKET_PORT = 9527
UDP_BROADCAST_PORT = 9530

UDP_DISCOVERY_TYPE = "voice_coding_server"

TYPE_TEXT = "text"
TYPE_PING = "ping"
TYPE_CONNECTED = "connected"
TYPE_ACK = "ack"
TYPE_PONG = "pong"
TYPE_SYNC_STATE = "sync_state"
TYPE_SYNC_DISABLED = "sync_disabled"

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


def build_ack_message() -> dict:
    return {
        "type": TYPE_ACK,
        "message": "Text received and typed",
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


def build_text_message(content: str) -> dict:
    return {
        "type": TYPE_TEXT,
        "content": content,
    }


def build_ping_message() -> dict:
    return {
        "type": TYPE_PING,
    }
