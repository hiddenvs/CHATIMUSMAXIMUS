import websocket
import json
import requests
from threading import Thread, Event
import html
from PyQt5 import QtCore

class Messager(QtCore.QObject):
    """
    Super trivial class to get around the issue with multiple inhertiance in
    PyQt
    """
    chat_signal = QtCore.pyqtSignal(str, str)
    def __init__(self, parent=None):
        super(Messager, self).__init__(parent)

    def recieve_chat_data(self, sender, message):
        self.chat_signal.emit(sender, message)

class SocketThread(Thread):
    # If only dameon threads are left, exit the program
    daemon = True
    def __init__(self, streamer_name, namespace='/chat', *args, **kwargs):
        self.socket = Socket(streamer_name, namespace)
        self.chat_signal = self.socket.chat_signal
        super(SocketThread, self).__init__(*args, **kwargs)

    def run(self):
        self.socket.run_forever(ping_interval=self.socket._heartbeat)

class Socket(websocket.WebSocketApp):
    def __init__(self, streamer_name, namespace='/chat'):
        self._streamer_name = streamer_name
        self.namespace = namespace 
        self._website_url = 'http://www.watchpeoplecode.com/socket.io/1/'
        key, heartbeat = self._connect_to_server_helper()
        self._heartbeat = heartbeat - 2
        
        # alters URL to be more websocket...ie
        self._website_socket = self._website_url.replace('http', 'ws') + 'websocket/'
        super(Socket, self).__init__(self._website_socket + key,
                                     on_open=self.on_open, on_close=self.on_close,
                                     on_message=self.on_message, 
                                     on_error=self.on_error)

        # use the trivial instance `_messager` to get around multiple inheritance
        # problems with PyQt
        self._messager = Messager()
        # Duck type the `chat_signal` onto the `Socket` instance/class
        self.chat_signal = self._messager.chat_signal

    def _reconnect_to_server(self):
        # NOTE: not sure if this is required
        #key, _ = self._connect_to_server_helper()
        #self.url =
        pass

    def _connect_to_server_helper(self):
        r = requests.post(self._website_url)
        params = r.text

        # unused variables are connection_timeout and supported_formats
        key, heartbeat_timeout, _, _ = params.split(':') 
        heartbeat_timeout = int(heartbeat_timeout)
        return key, heartbeat_timeout

    def on_open(self, *args):
        print('Websocket open!')

    def on_close(self, *args):
        print('Websocket closed!')
        # TODO: Retry the socket

    def _ping_server(self):
        # this pings the server
        self.send_packet_helper(2)
    
    def on_message(self, *args):
        message = args[1].split(':', 3)
        key = int(message[0])
        namespace = message[2]

        if len(message) >= 4:
           data = message[3]
        else:
            data = ''
        if key == 1 and args[1] == '1::':
            self.send_packet_helper(1)
        elif key == 1 and args[1] == '1::{}'.format(self.namespace):
            self.send_packet_helper(5, data={'name':'initialize'})
            data = {'name':'join', 'args':['{}'.format(self._streamer_name)]}
            self.send_packet_helper(5, data=data)
        elif key  == 5:
            data = json.loads(data, )
            if data['name'] == 'message':
                message = data['args'][0]
                sender = html.unescape(message['sender'])
                message = html.unescape(message['text'])
                self._messager.recieve_chat_data(sender, message)

    def on_error(self, *args):
        print(args[1])

    def disconnect(self):
        callback = ''
        data = ''
        # '1::namespace'
        self.send(':'.join([str(self.TYPE_KEYS['DISCONNECT']), 
                           callback, self.namespace, data]))

    def send_packet_helper(self, 
                           type_key, 
                           data=None):

        if data is None:
            data = ''
        else:
            data = json.dumps(data)
        
        # NOTE: callbacks currently not implemented
        callback = ''
        message = ':'.join([str(type_key), callback, self.namespace, data])
        self.send(message)
    
if __name__ == '__main__':
    streamer_name = 'beohoff'
    # this is default for the flask app
    socket = Socket(streamer_name)
    socket.run_forever()