import os
import yaml
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


def get_base_dir():
    cwd = os.getcwd()
    base_cwd = os.path.basename(cwd)
    if base_cwd == 'scripts':
        return '..'
    elif base_cwd == 'acceptance' or base_cwd == 'vagrant':
        return '.'
    else:
        raise RuntimeError("Run from the 'acceptance (or vagrant)' directory")


def read_yaml(yaml_file):
    with open(yaml_file) as f:
        return yaml.load(f)


def get_nodes(base_dir):
    config_file = os.path.join(base_dir, 'default-config.yaml')
    data = read_yaml(config_file)
    nodes = data.get('nodes')
    if not nodes:
        raise RuntimeError('Bad config file: missing nodes')
    return nodes


def get_all_tests(base_dir):
    all_tests = []
    td = os.path.join(base_dir, 'tests')
    for f in os.listdir(td):
        if f.endswith(".yaml"):
            tf = os.path.join(td, f)
            all_tests.append(tf)
    return all_tests


class ClaraTest:

    def __init__(self, client, data, item):
        pass

    def run(self):
        pass


class ClaraTestSuite:

    def __init__(self, client, test_file):
        pass

    def run_tests(self):
        pass


class ClaraTestRunner():

    def __init__(self):
        pass

    def start_client(self, nodes):
        pass

    def stop_client(self):
        pass

    def run_all_tests(self, test_files):
        pass

    def print_report(self):
        pass
