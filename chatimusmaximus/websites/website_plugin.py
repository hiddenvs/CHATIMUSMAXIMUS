import os
import re
import sys
import signal
import asyncio
from parse import parse
from PyQt5 import QtCore
from pluginmanager import IPlugin


class WebsitePlugin(QtCore.QObject):
    chat_signal = QtCore.pyqtSignal(str, str, str)
    connected_signal = QtCore.pyqtSignal(bool, str)

    def __init__(self, platform, parent=None):
        super().__init__(parent)
        self.platform = platform
        # TODO: change from `process` to `subprocess`
        self.process = None

    def start_subprocess(self, path_script, *args, **kwargs):
        self.process = asyncio.ensure_future(asyncio.create_subprocess_exec(
            sys.executable,
            path_script,
            stdin=sys.stdin,
            stderr=sys.stderr,
            preexec_fn=os.setsid,
            *args,
            **kwargs))

        asyncio.ensure_future(self._reoccuring())

    @asyncio.coroutine
    def _reoccuring(self):
        while True:
            print('loop', type(self.process))
            if self.process is None or isinstance(self.process, asyncio.Task):
                yield from asyncio.sleep(3)
            else:
                print('made it here')
                std_out = self.process.communicate()[0]
                print('std out', std_out)
                self._parse_communication(std_out)
                yield from asyncio.sleep(1)

    def _parse_communication(self, comms):
        for comm in comms:
            command, body = comm.split(sep=' ', maxsplit=1)
            print('command body pair', command, body)
            if command == 'MSG':
                nick, message = parse('NICK: {} BODY: {}', body)
                self.chat_signal.emit(nick, message, self.platform)
            elif command == 'CONNECTED':
                self.connected_signal.emit(True, self.platform)
            elif command == 'DISCONNECTED':
                self.connected_signal.emit(False, self.platform)


# NOTE: Forcing `WebsitePlugin` to be subclass of IPlugin
# for ease of parsing
IPlugin.register(WebsitePlugin)


