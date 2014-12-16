import logging
import os
import re
import yaml
import zmq

logging.basicConfig()
log = logging.getLogger("ACCEPTANCE")

port = "7788"
standard_requests = (
    'list-dpes'
)


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


def parse_action(action, item='java'):

    def create_msg(action, lang, instance):
        return ':'.join(['clara', action, lang, instance])

    action = action.replace('{{item}}', item)
    act_re = '(start|stop)'
    lang_re = '(java|python|cpp)'

    m = re.search(r'%s\s+(%s\s+)?platform' % (act_re, lang_re), action)
    if m:
        if m.group(3):
            lang = m.group(3)
        else:
            lang = 'java'
        return 'platform', create_msg(m.group(1), lang, 'platform')

    m = re.search(r'%s\s+%s\s+dpe\s+on\s+(\w+)' % (act_re, lang_re), action)
    if m:
        return m.group(3), create_msg(m.group(1), m.group(2), 'dpe')

    req_re = '(list\s+(dpes))'
    m = re.search(r'request\s+(%s\s+)?%s(\s+on\s+(\w+))?' % (lang_re, req_re),
                  action)
    if m:
        if m.group(2):
            lang = m.group(2)
        else:
            lang = 'java'
        request = '-'.join(m.group(3).split())
        if request not in standard_requests:
            raise ClaraRequestError('Request not supported: "%s"' % request)
        if m.group(6):
            node = m.group(6)
        else:
            node = 'platform'
        return node, create_msg('request', lang, request)

    raise ClaraRequestError('Malformed action: "%s"' % action)


class ClaraTest:

    def __init__(self, client, data, item):
        self._client = client
        self._actions = data.get('actions')
        self._result = data.get('result')
        self._item = item

    def run(self):
        result = None
        if not self._actions:
            raise ClaraRequestError('The test has no actions')
        if self._result is None:
            raise ClaraRequestError('The test has no result')
        for action in self._actions:
            log.info("Request '%s'" % action)
            node, msg = parse_action(action, self._item)
            result = self._client.request(node, msg)
        if result == self._result:
            log.info("Result %s" % result)
            return result
        else:
            raise ClaraRequestError('Wrong result: "%s". Expected: "%s"' %
                                    (result, self._result))


class ClaraTestSuite:

    def __init__(self, client, test_file):
        data = read_yaml(test_file)
        test_name = os.path.basename(test_file).replace('.yaml', '')

        self._name = data.get("name", test_name)
        self._tests = data.get("tests")
        self._context = data.get("with", ['java'])
        self._client = client

    def run_tests(self):
        if not self._tests:
            log.error("Missing tests")
            return (False, self._name)
        try:
            log.info("Running %s" % self._name)
            for item in self._context:
                for data in self._tests:
                    test = ClaraTest(self._client, data, item)
                    test.run()
            return (True, self._name)
        except ClaraRequestError as e:
            log.error(str(e))
            return (False, self._name)
        finally:
            self._client.request_all('clara:stop:all:all')


class ClaraTestRunner():

    def __init__(self, nodes, tests):
        self._nodes = nodes
        self._tests = tests
        self._report = []
        self._client = None

    def start_client(self):
        ctx = zmq.Context()
        self._client = ClaraDaemonClient(ctx, self._nodes)

    def stop_client(self):
        pass

    def run_all_tests(self):
        self._report = []
        for test_file in self._tests:
            test_suite = ClaraTestSuite(self._client, test_file)
            status = test_suite.run_tests()
            self._report.append(status)
        return self._report

    def print_report(self):
        pass


if __name__ == '__main__':

    base = get_base_dir()
    nodes = get_nodes(base)
    tests = get_all_tests(base)

    log.setLevel(logging.INFO)

    tr = ClaraTestRunner(nodes, tests)
    tr.start_client()
    tr.run_all_tests()
