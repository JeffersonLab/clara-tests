import zmq

port = "7788"


class ClaraRequestError(Exception):
    pass


class ClaraDaemonClient():

    def __init__(self, context, nodes):
        self._sockets = {}
        for name, ip in nodes.items():
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://%s:%s" % (ip, port))
            self._sockets[name] = socket

    def request(self, node, msg):
        socket = self._sockets.get(node)
        if not socket:
            raise ClaraRequestError('Bad node: "%s"' % node)
        if not msg:
            raise ClaraRequestError('Empty message')
        return self._request(socket, msg)

    def request_all(self, msg):
        for socket in self._sockets.values():
            self._request(socket, msg)

    def _request(self, socket, msg):
        socket.send(msg)
        res = socket.recv_multipart()
        if not res:
            raise ClaraRequestError('Empty response')
        if len(res) < 2:
            raise ClaraRequestError('Bad response: "%s"' % str(res))
        status, text = res[0], res[1:]
        if status == 'ERROR':
            if ''.join(text) == '':
                raise ClaraRequestError('Empty error')
            raise ClaraRequestError('\n'.join(text))
        if status != 'SUCCESS':
            raise ClaraRequestError('Bad status: "%s"' % status)
        return text
