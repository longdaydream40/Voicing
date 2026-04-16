from __future__ import annotations

import asyncio
import ctypes
import json
import logging
import os
import socket
import threading
import uuid
from dataclasses import dataclass
from typing import Callable

from platform_utils import get_platform
from voicing_protocol import (
    BLUETOOTH_MESSAGE_DELIMITER,
    BLUETOOTH_RFCOMM_CHANNEL,
    BLUETOOTH_SERVICE_UUID,
)

BLUETOOTH_SERVICE_NAME = "Voicing"
BLUETOOTH_MESSAGE_DELIMITER_BYTES = BLUETOOTH_MESSAGE_DELIMITER.encode("utf-8")
LINUX_PROFILE_OBJECT_PATH = "/com/kevinlasnh/voicing/profile"
WINDOWS_BLUETOOTH_NAMESPACE = 16
RNRSERVICE_REGISTER = 0
RNRSERVICE_DELETE = 1


class BluetoothRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class BluetoothClientInfo:
    label: str
    device_path: str | None = None


class BluetoothClientAdapter:
    def __init__(self, client_socket: socket.socket, info: BluetoothClientInfo):
        self.socket = client_socket
        self.info = info
        self._send_lock = threading.Lock()
        self._closed = False

    def send_message(self, message: dict) -> None:
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8") + BLUETOOTH_MESSAGE_DELIMITER_BYTES
        with self._send_lock:
            self.socket.sendall(payload)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self.socket.close()
        except OSError:
            pass

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return f"BluetoothClientAdapter({self.info.label})"


def split_bluetooth_messages(buffer: bytearray, chunk: bytes) -> list[str]:
    buffer.extend(chunk)
    messages: list[str] = []
    while True:
        delimiter_index = buffer.find(BLUETOOTH_MESSAGE_DELIMITER_BYTES)
        if delimiter_index < 0:
            break
        raw_message = bytes(buffer[:delimiter_index])
        del buffer[: delimiter_index + len(BLUETOOTH_MESSAGE_DELIMITER_BYTES)]
        if raw_message:
            messages.append(raw_message.decode("utf-8"))
    return messages


def start_bluetooth_server(
    state,
    message_handler: Callable[[dict], list[dict]],
    welcome_message_factory: Callable[[], dict],
) -> None:
    platform_name = get_platform()
    if platform_name == "windows":
        server = _WindowsBluetoothServer(state, message_handler, welcome_message_factory)
        server.run()
        return

    if platform_name == "linux":
        server = _LinuxBluetoothServer(state, message_handler, welcome_message_factory)
        server.run()
        return

    raise BluetoothRuntimeError("Bluetooth transport is only available on Windows and Linux.")


def is_bluetooth_desktop_platform() -> bool:
    return get_platform() in {"windows", "linux"}


def _handle_client_loop(state, client: BluetoothClientAdapter, message_handler: Callable[[dict], list[dict]]) -> None:
    buffer = bytearray()
    with state.lock:
        state.connected_clients.add(client)
    logging.info("Bluetooth client connected: %s", client.info.label)
    try:
        while state.running:
            chunk = client.socket.recv(4096)
            if not chunk:
                break
            for text_message in split_bluetooth_messages(buffer, chunk):
                try:
                    responses = message_handler(json.loads(text_message))
                except json.JSONDecodeError:
                    logging.warning("Bluetooth message is not valid JSON: %s", text_message)
                    continue
                for response in responses:
                    client.send_message(response)
    except OSError as exc:
        logging.warning("Bluetooth client %s disconnected: %s", client.info.label, exc)
    finally:
        with state.lock:
            state.connected_clients.discard(client)
        client.close()
        logging.info("Bluetooth client disconnected: %s", client.info.label)


def _spawn_client_handler(state, client: BluetoothClientAdapter, message_handler: Callable[[dict], list[dict]]) -> None:
    thread = threading.Thread(
        target=_handle_client_loop,
        args=(state, client, message_handler),
        daemon=True,
    )
    thread.start()


class _WindowsBluetoothServer:
    def __init__(self, state, message_handler, welcome_message_factory):
        self.state = state
        self.message_handler = message_handler
        self.welcome_message_factory = welcome_message_factory
        self._service_registration: _WindowsServiceRegistration | None = None

    def run(self) -> None:
        try:
            server_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        except OSError as exc:
            raise BluetoothRuntimeError(f"Windows Bluetooth socket unavailable: {exc}") from exc

        try:
            server_socket.bind((socket.BDADDR_ANY, BLUETOOTH_RFCOMM_CHANNEL))
            server_socket.listen(1)
            local_address = server_socket.getsockname()[0]
            self._service_registration = _WindowsServiceRegistration(local_address)
            self._service_registration.register()
            logging.info(
                "Windows Bluetooth RFCOMM server started at %s channel %s",
                local_address,
                BLUETOOTH_RFCOMM_CHANNEL,
            )

            while self.state.running:
                try:
                    client_socket, client_address = server_socket.accept()
                except OSError as exc:
                    if self.state.running:
                        logging.error("Windows Bluetooth accept failed: %s", exc)
                    break

                client = BluetoothClientAdapter(
                    client_socket,
                    BluetoothClientInfo(label=str(client_address[0])),
                )
                client.send_message(self.welcome_message_factory())
                _spawn_client_handler(self.state, client, self.message_handler)
        finally:
            if self._service_registration is not None:
                self._service_registration.unregister()
            server_socket.close()


class _LinuxBluetoothServer:
    def __init__(self, state, message_handler, welcome_message_factory):
        self.state = state
        self.message_handler = message_handler
        self.welcome_message_factory = welcome_message_factory

    def run(self) -> None:
        asyncio.run(self._run_async())

    async def _run_async(self) -> None:
        try:
            from dbus_fast import BusType, Variant
            from dbus_fast.aio import MessageBus
            from dbus_fast.annotations import DBusUnixFd
            from dbus_fast.service import ServiceInterface, method
        except ImportError as exc:
            raise BluetoothRuntimeError("dbus-fast is required for Linux Bluetooth support.") from exc

        server = self

        class VoicingProfile(ServiceInterface):
            def __init__(self):
                super().__init__("org.bluez.Profile1")

            @method()
            def Release(self) -> None:
                logging.info("BlueZ profile released")

            @method()
            def NewConnection(self, device: "o", fd: DBusUnixFd, fd_properties: "a{sv}") -> None:
                client_socket = socket.fromfd(fd, socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                os.close(fd)
                client = BluetoothClientAdapter(
                    client_socket,
                    BluetoothClientInfo(label=device, device_path=device),
                )
                client.send_message(server.welcome_message_factory())
                _spawn_client_handler(server.state, client, server.message_handler)

            @method()
            def RequestDisconnection(self, device: "o") -> None:
                logging.info("BlueZ requested disconnection for %s", device)

        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        profile = VoicingProfile()
        bus.export(LINUX_PROFILE_OBJECT_PATH, profile)

        bluez_introspection = await bus.introspect("org.bluez", "/org/bluez")
        bluez_object = bus.get_proxy_object("org.bluez", "/org/bluez", bluez_introspection)
        profile_manager = bluez_object.get_interface("org.bluez.ProfileManager1")

        options = {
            "Name": Variant("s", BLUETOOTH_SERVICE_NAME),
            "Service": Variant("s", BLUETOOTH_SERVICE_UUID),
            "Role": Variant("s", "server"),
            "Channel": Variant("q", BLUETOOTH_RFCOMM_CHANNEL),
            "RequireAuthentication": Variant("b", False),
            "RequireAuthorization": Variant("b", False),
            "AutoConnect": Variant("b", True),
        }

        await profile_manager.call_register_profile(
            LINUX_PROFILE_OBJECT_PATH,
            BLUETOOTH_SERVICE_UUID,
            options,
        )
        logging.info(
            "Linux Bluetooth RFCOMM profile registered at channel %s with UUID %s",
            BLUETOOTH_RFCOMM_CHANNEL,
            BLUETOOTH_SERVICE_UUID,
        )

        try:
            while self.state.running:
                await asyncio.sleep(1)
        finally:
            try:
                await profile_manager.call_unregister_profile(LINUX_PROFILE_OBJECT_PATH)
            except Exception as exc:  # pragma: no cover - best effort cleanup
                logging.warning("Failed to unregister BlueZ profile: %s", exc)
            bus.disconnect()


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_uuid(cls, value: str) -> "GUID":
        parsed = uuid.UUID(value)
        data4 = (ctypes.c_ubyte * 8)(*parsed.bytes[8:])
        return cls(parsed.time_low, parsed.time_mid, parsed.time_hi_version, data4)


class SOCKADDR(ctypes.Structure):
    _fields_ = [
        ("sa_family", ctypes.c_ushort),
        ("sa_data", ctypes.c_char * 14),
    ]


class SOCKADDR_BTH(ctypes.Structure):
    _fields_ = [
        ("addressFamily", ctypes.c_ushort),
        ("btAddr", ctypes.c_ulonglong),
        ("serviceClassId", GUID),
        ("port", ctypes.c_uint32),
    ]


class SOCKET_ADDRESS(ctypes.Structure):
    _fields_ = [
        ("lpSockaddr", ctypes.POINTER(SOCKADDR)),
        ("iSockaddrLength", ctypes.c_int),
    ]


class CSADDR_INFO(ctypes.Structure):
    _fields_ = [
        ("LocalAddr", SOCKET_ADDRESS),
        ("RemoteAddr", SOCKET_ADDRESS),
        ("iSocketType", ctypes.c_int),
        ("iProtocol", ctypes.c_int),
    ]


class WSAQUERYSETW(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_uint32),
        ("lpszServiceInstanceName", ctypes.c_wchar_p),
        ("lpServiceClassId", ctypes.POINTER(GUID)),
        ("lpVersion", ctypes.c_void_p),
        ("lpszComment", ctypes.c_wchar_p),
        ("dwNameSpace", ctypes.c_uint32),
        ("lpNSProviderId", ctypes.c_void_p),
        ("lpszContext", ctypes.c_wchar_p),
        ("dwNumberOfProtocols", ctypes.c_uint32),
        ("lpafpProtocols", ctypes.c_void_p),
        ("lpszQueryString", ctypes.c_wchar_p),
        ("dwNumberOfCsAddrs", ctypes.c_uint32),
        ("lpcsaBuffer", ctypes.POINTER(CSADDR_INFO)),
        ("dwOutputFlags", ctypes.c_uint32),
        ("lpBlob", ctypes.c_void_p),
    ]


class _WindowsServiceRegistration:
    def __init__(self, local_address: str):
        self.local_address = local_address
        self.guid = GUID.from_uuid(BLUETOOTH_SERVICE_UUID)
        self.ws2_32 = ctypes.windll.Ws2_32
        self._queryset = None
        self._local_sockaddr = None
        self._remote_sockaddr = None
        self._csaddr = None

    def register(self) -> None:
        self._queryset = self._build_queryset()
        result = self.ws2_32.WSASetServiceW(ctypes.byref(self._queryset), RNRSERVICE_REGISTER, 0)
        if result != 0:
            raise BluetoothRuntimeError(
                f"WSASetService register failed: {ctypes.WinError(ctypes.get_last_error())}"
            )

    def unregister(self) -> None:
        if self._queryset is None:
            return
        self.ws2_32.WSASetServiceW(ctypes.byref(self._queryset), RNRSERVICE_DELETE, 0)

    def _build_queryset(self) -> WSAQUERYSETW:
        self._local_sockaddr = SOCKADDR_BTH(
            addressFamily=socket.AF_BLUETOOTH,
            btAddr=_mac_to_bth_addr(self.local_address),
            serviceClassId=self.guid,
            port=BLUETOOTH_RFCOMM_CHANNEL,
        )
        self._remote_sockaddr = SOCKADDR_BTH(
            addressFamily=socket.AF_BLUETOOTH,
            btAddr=0,
            serviceClassId=self.guid,
            port=0,
        )

        local_ptr = ctypes.cast(ctypes.pointer(self._local_sockaddr), ctypes.POINTER(SOCKADDR))
        remote_ptr = ctypes.cast(ctypes.pointer(self._remote_sockaddr), ctypes.POINTER(SOCKADDR))
        self._csaddr = CSADDR_INFO(
            LocalAddr=SOCKET_ADDRESS(local_ptr, ctypes.sizeof(SOCKADDR_BTH)),
            RemoteAddr=SOCKET_ADDRESS(remote_ptr, ctypes.sizeof(SOCKADDR_BTH)),
            iSocketType=socket.SOCK_STREAM,
            iProtocol=socket.BTPROTO_RFCOMM,
        )

        return WSAQUERYSETW(
            dwSize=ctypes.sizeof(WSAQUERYSETW),
            lpszServiceInstanceName=BLUETOOTH_SERVICE_NAME,
            lpServiceClassId=ctypes.pointer(self.guid),
            lpVersion=None,
            lpszComment=None,
            dwNameSpace=WINDOWS_BLUETOOTH_NAMESPACE,
            lpNSProviderId=None,
            lpszContext=None,
            dwNumberOfProtocols=0,
            lpafpProtocols=None,
            lpszQueryString=None,
            dwNumberOfCsAddrs=1,
            lpcsaBuffer=ctypes.pointer(self._csaddr),
            dwOutputFlags=0,
            lpBlob=None,
        )


def _mac_to_bth_addr(address: str) -> int:
    return int(address.replace(":", "").replace("-", ""), 16)
