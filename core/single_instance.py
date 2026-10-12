"""Single-instance guard built on QLocalServer (named pipe on Windows).

The pipe disappears with the process, so a crash can never leave a stale lock.
A second launch connects to the running instance, asks it to show itself and
exits.
"""
from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

log = logging.getLogger("ruby.single_instance")

DEFAULT_KEY = "RubyAI-single-instance-v1"


class SingleInstance(QObject):
    activation_requested = pyqtSignal(str)

    def __init__(self, key: str = DEFAULT_KEY, parent=None):
        super().__init__(parent)
        self.key = key
        self._server: QLocalServer | None = None
        self._clients: list[QLocalSocket] = []

    def _notify_existing(self, command: str = "show", timeout_ms: int = 500) -> bool:
        sock = QLocalSocket()
        sock.connectToServer(self.key)
        if not sock.waitForConnected(timeout_ms):
            return False
        sock.write((command + "\n").encode("utf-8"))
        sock.flush()
        sock.waitForBytesWritten(timeout_ms)
        sock.disconnectFromServer()
        return True

    def try_acquire(self) -> bool:
        """True if this process is now the primary instance."""
        if self._notify_existing():
            return False
        QLocalServer.removeServer(self.key)  # clears a stale unix socket; no-op on Windows
        server = QLocalServer(self)
        if not server.listen(self.key):
            # Lost a launch race: the other process may have just won.
            if self._notify_existing():
                return False
            log.warning("Single-instance server failed (%s); continuing unguarded", server.errorString())
            return True
        server.newConnection.connect(self._on_connection)
        self._server = server
        return True

    def _on_connection(self) -> None:
        while self._server and self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            self._clients.append(sock)
            sock.readyRead.connect(lambda s=sock: self._read(s))
            sock.disconnected.connect(lambda s=sock: self._drop(s))
            if sock.bytesAvailable():
                self._read(sock)

    def _read(self, sock: QLocalSocket) -> None:
        data = bytes(sock.readAll()).decode("utf-8", "ignore")
        for line in data.splitlines():
            if line.strip():
                self.activation_requested.emit(line.strip())

    def _drop(self, sock: QLocalSocket) -> None:
        if sock in self._clients:
            self._clients.remove(sock)
        sock.deleteLater()

    def release(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server.deleteLater()
            self._server = None
        for sock in list(self._clients):
            sock.abort()
            self._drop(sock)
