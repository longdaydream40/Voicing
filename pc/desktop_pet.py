from __future__ import annotations

import logging
import os
import sys
import ctypes
from ctypes import wintypes
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageSequence
from PyQt5.QtCore import QAbstractNativeEventFilter, QPoint, QSize, Qt, QTimer
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget


DEFAULT_MAX_SIZE = QSize(280, 360)
CLICK_EFFECT_SIZE = QSize(46, 46)
CLICK_EFFECT_OFFSET = QPoint(16, -12)
SUPPORTED_IMAGE_SUFFIXES = {".png", ".webp", ".gif", ".apng"}
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
DEFAULT_PET_HOTKEY_ID = 0x5650
DEFAULT_PET_HOTKEY_MODIFIERS = MOD_CONTROL | MOD_ALT
DEFAULT_PET_HOTKEY_KEY = ord("V")


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_default_pet_asset_path() -> Path | None:
    assets_dir = get_runtime_base_dir() / "assets"
    candidates = (
        "desktop_pet.apng",
        "desktop_pet.gif",
        "desktop_pet.png",
        "pet_idle.apng",
        "pet_idle.gif",
        "pet_idle.png",
        "pet.apng",
        "pet.gif",
        "pet.png",
        "icon_1024.png",
    )
    for name in candidates:
        path = assets_dir / name
        if path.exists():
            return path
    return None


def _scaled_size(original: QSize, max_size: QSize) -> QSize:
    if original.isEmpty():
        return max_size
    return original.scaled(max_size, Qt.KeepAspectRatio)


def get_default_click_effect_path() -> Path | None:
    path = get_runtime_base_dir() / "assets" / "desktop_pet_click.png"
    return path if path.exists() else None


def force_window_topmost(widget: QWidget) -> None:
    if sys.platform.startswith("win"):
        try:
            hwnd = int(widget.winId())
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
            return
        except Exception as exc:
            logging.debug("Failed to force topmost window: %s", exc)
    widget.raise_()


class ClickEffectPopup(QWidget):
    """Small transparent click indicator shown near the desktop pet."""

    def __init__(self, icon_path: str | os.PathLike, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setStyleSheet("background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                CLICK_EFFECT_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.label.setPixmap(pixmap)
            self.resize(pixmap.size())
        else:
            self.resize(CLICK_EFFECT_SIZE)
        self.label.setGeometry(self.rect())

    def show_at(self, global_pos: QPoint) -> None:
        self.move(global_pos)
        self.setWindowOpacity(1.0)
        self.show()
        force_window_topmost(self)


class WindowsGlobalHotkey(QAbstractNativeEventFilter):
    """Windows RegisterHotKey bridge for raising the desktop pet."""

    def __init__(
        self,
        callback,
        *,
        hotkey_id: int = DEFAULT_PET_HOTKEY_ID,
        modifiers: int = DEFAULT_PET_HOTKEY_MODIFIERS,
        key: int = DEFAULT_PET_HOTKEY_KEY,
    ):
        super().__init__()
        self.callback = callback
        self.hotkey_id = hotkey_id
        self.modifiers = modifiers
        self.key = key
        self.registered = False

    def register(self) -> bool:
        if not sys.platform.startswith("win"):
            return False
        try:
            self.registered = bool(
                ctypes.windll.user32.RegisterHotKey(
                    None,
                    self.hotkey_id,
                    self.modifiers,
                    self.key,
                )
            )
        except Exception as exc:
            logging.warning("Failed to register desktop pet hotkey: %s", exc)
            self.registered = False
        return self.registered

    def unregister(self) -> None:
        if self.registered and sys.platform.startswith("win"):
            try:
                ctypes.windll.user32.UnregisterHotKey(None, self.hotkey_id)
            except Exception:
                pass
        self.registered = False

    def nativeEventFilter(self, event_type, message):
        if event_type != "windows_generic_MSG":
            return False, 0
        try:
            msg = _MSG.from_address(int(message))
        except Exception:
            return False, 0
        if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
            self.callback()
            return True, 0
        return False, 0


class DesktopPetWindow(QWidget):
    """Transparent always-on-top window for PNG/GIF desktop pet assets."""

    def __init__(self, asset_path: str | os.PathLike | None = None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setStyleSheet("background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)

        self._movie: QMovie | None = None
        self._pixmap: QPixmap | None = None
        self._frames: list[tuple[QPixmap, int]] = []
        self._frame_index = 0
        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._show_next_frame)
        self._topmost_timer = QTimer(self)
        self._topmost_timer.timeout.connect(lambda: force_window_topmost(self))
        self._click_effect: ClickEffectPopup | None = None
        self._click_effect_path = get_default_click_effect_path()
        self._drag_offset: QPoint | None = None
        self._press_global_pos: QPoint | None = None
        self._was_dragged = False
        self._asset_path: Path | None = None
        self._max_size = DEFAULT_MAX_SIZE

        self.load_asset(asset_path or get_default_pet_asset_path())

    @property
    def asset_path(self) -> Path | None:
        return self._asset_path

    def load_asset(self, asset_path: str | os.PathLike | None) -> bool:
        self._stop_movie()
        self._pixmap = None
        self._asset_path = Path(asset_path) if asset_path else None

        if self._asset_path is None or not self._asset_path.exists():
            logging.warning("Desktop pet asset not found: %s", self._asset_path)
            self._show_placeholder()
            return False

        suffix = self._asset_path.suffix.lower()
        if suffix not in SUPPORTED_IMAGE_SUFFIXES:
            logging.warning("Unsupported desktop pet asset type: %s", self._asset_path)
            self._show_placeholder()
            return False

        if suffix == ".gif":
            return self._load_movie(self._asset_path)
        if suffix == ".apng":
            return self._load_apng(self._asset_path)
        return self._load_pixmap(self._asset_path)

    def show_pet(self) -> None:
        if self.isVisible():
            force_window_topmost(self)
            return
        if self.pos().isNull():
            self.move_to_default_position()
        self.show()
        force_window_topmost(self)
        self._topmost_timer.start(1000)

    def showEvent(self, event):
        super().showEvent(event)
        force_window_topmost(self)

    def hide_pet(self) -> None:
        self._hide_click_effect()
        self._topmost_timer.stop()
        self.hide()

    def raise_pet(self) -> None:
        if not self.isVisible():
            self.show_pet()
            return
        self.show()
        force_window_topmost(self)
        if self._click_effect is not None and self._click_effect.isVisible():
            force_window_topmost(self._click_effect)

    def toggle_pet(self) -> bool:
        if self.isVisible():
            self.hide_pet()
            return False
        self.show_pet()
        return True

    def move_to_default_position(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            self.move(80, 80)
            return
        geometry = screen.availableGeometry()
        self.adjustSize()
        x = geometry.right() - self.width() - 48
        y = geometry.bottom() - self.height() - 48
        self.move(max(geometry.left(), x), max(geometry.top(), y))

    def resizeEvent(self, event):
        self.label.setGeometry(self.rect())
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._press_global_pos = event.globalPos()
            self._was_dragged = False
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            if self._press_global_pos is not None:
                moved = event.globalPos() - self._press_global_pos
                if abs(moved.x()) > 4 or abs(moved.y()) > 4:
                    self._was_dragged = True
            self.move(event.globalPos() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._was_dragged:
                self._toggle_click_effect()
            self._drag_offset = None
            self._press_global_pos = None
            self._was_dragged = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _play_click_effect(self) -> None:
        if self._click_effect_path is None or not self._click_effect_path.exists():
            return
        popup = ClickEffectPopup(self._click_effect_path)
        self._click_effect = popup
        popup.show_at(self.mapToGlobal(QPoint(0, 0)) + CLICK_EFFECT_OFFSET)

    def _toggle_click_effect(self) -> None:
        if self._click_effect is not None and self._click_effect.isVisible():
            self._hide_click_effect()
            return
        self._play_click_effect()

    def _hide_click_effect(self) -> None:
        if self._click_effect is not None:
            self._click_effect.close()
            self._click_effect = None

    def _load_movie(self, path: Path) -> bool:
        movie = QMovie(str(path))
        if not movie.isValid():
            logging.warning("Invalid desktop pet GIF: %s", path)
            self._show_placeholder()
            return False

        movie.jumpToFrame(0)
        original_size = movie.frameRect().size()
        if original_size.isEmpty():
            original_size = movie.currentPixmap().size()
        scaled = _scaled_size(original_size, self._max_size)
        movie.setScaledSize(scaled)
        self.label.setMovie(movie)
        self.resize(scaled)
        self.label.setGeometry(self.rect())
        self._movie = movie
        movie.start()
        return True

    def _load_pixmap(self, path: Path) -> bool:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logging.warning("Invalid desktop pet image: %s", path)
            self._show_placeholder()
            return False

        scaled = _scaled_size(pixmap.size(), self._max_size)
        pixmap = pixmap.scaled(scaled, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._pixmap = pixmap
        self.label.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.label.setGeometry(self.rect())
        return True

    def _load_apng(self, path: Path) -> bool:
        try:
            image = Image.open(path)
            frames: list[tuple[QPixmap, int]] = []
            for frame in ImageSequence.Iterator(image):
                pixmap = self._pil_frame_to_pixmap(frame.convert("RGBA"))
                if pixmap.isNull():
                    continue
                scaled = _scaled_size(pixmap.size(), self._max_size)
                pixmap = pixmap.scaled(scaled, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                duration = int(frame.info.get("duration", image.info.get("duration", 100)) or 100)
                frames.append((pixmap, max(20, duration)))
        except Exception as exc:
            logging.warning("Invalid desktop pet APNG %s: %s", path, exc)
            self._show_placeholder()
            return False

        if not frames:
            logging.warning("Desktop pet APNG has no usable frames: %s", path)
            self._show_placeholder()
            return False

        self._frames = frames
        self._frame_index = 0
        self.label.setPixmap(frames[0][0])
        self.resize(frames[0][0].size())
        self.label.setGeometry(self.rect())
        if len(frames) > 1:
            self._frame_timer.start(frames[0][1])
        return True

    def _show_next_frame(self) -> None:
        if not self._frames:
            self._frame_timer.stop()
            return
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        pixmap, duration = self._frames[self._frame_index]
        self.label.setPixmap(pixmap)
        if self.size() != pixmap.size():
            self.resize(pixmap.size())
            self.label.setGeometry(self.rect())
        self._frame_timer.start(duration)

    def _pil_frame_to_pixmap(self, frame: Image.Image) -> QPixmap:
        buffer = BytesIO()
        frame.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        return pixmap

    def _show_placeholder(self) -> None:
        self.label.setText("Desktop Pet")
        self.label.setStyleSheet(
            "QLabel {"
            "color: white;"
            "background-color: rgba(32, 32, 32, 220);"
            "border: 1px solid rgba(255, 255, 255, 60);"
            "border-radius: 12px;"
            "padding: 12px;"
            "font: 13px 'Segoe UI';"
            "}"
        )
        self.resize(128, 48)
        self.label.setGeometry(self.rect())

    def _stop_movie(self) -> None:
        self._frame_timer.stop()
        self._frames = []
        self._frame_index = 0
        if self._movie is not None:
            self._movie.stop()
            self._movie.deleteLater()
            self._movie = None
