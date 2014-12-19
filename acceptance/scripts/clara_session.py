#!/usr/bin/env python

import os
import sys
import subprocess


class TmuxWrapper:
    def __init__(self, session_name):
        self.sn = session_name

    def has_session(self):
        with open(os.devnull, 'wb') as DEVNULL:
            cmd = 'has-session -t %s' % self.sn
            rc = self.call(cmd, stderr=DEVNULL)
            return rc == 0

    def new_session(self, win_name, win_dir=None, check_dir=False):
        cmd = 'new-session -s %s -n %s -d' % (self.sn, win_name)
        return self._create_on_directory(cmd, win_dir, check_dir)

    def new_window(self, win_num, win_name, win_dir=None, check_dir=False):
        cmd = 'new-window -t %s:%s -n %s -d' % (self.sn, win_num, win_name)
        return self._create_on_directory(cmd, win_dir, check_dir)

    def split_v(self, win_num, win_dir=None, check_dir=None):
        cmd = 'split-window -v -t %s:%s' % (self.sn, win_num)
        return self._create_on_directory(cmd, win_dir, check_dir)

    def split_h(self, win_num, win_dir=None, check_dir=None):
        cmd = 'split-window -h -t %s:%s' % (self.sn, win_num)
        return self._create_on_directory(cmd, win_dir, check_dir)

    def select_window(self, win_num):
        cmd = 'select-window -t %s:%s' % (self.sn, win_num)
        return self.call(cmd)

    def run_command(self, win_num, cmd):
        cmd = 'send-keys -R -t %s:%s "%s" Enter' % (self.sn, win_num, cmd)
        return self.call(cmd)

    def attach(self):
        cmd = 'attach-session -t %s' % self.sn
        return self.call(cmd)

    def call(self, cmd, **kwargs):
        tmux_cmd = "tmux -2 %s" % cmd
        kwargs['shell'] = True
        return subprocess.call(tmux_cmd, **kwargs)

    def _create_on_directory(self, cmd, win_dir, check_dir):
        work_dir = os.path.expanduser(win_dir)
        if check_dir and not os.path.isdir(work_dir):
            print "Directory does not exist: %s" % win_dir
            return False
        cmd = "%s 'cd %s; exec ${SHELL:-sh}'" % (cmd, work_dir)
        return self.call(cmd)


def create_session(tw):
    print "No session found. Creating and configuring."

    tw.new_session('base', '/vagrant/acceptance/')

    tw.new_window(3, 'java', '~/clara/dev/clara-java', True)
    tw.new_window(4, 'cpp', '~/clara/dev/clara-cpp', True)
    tw.new_window(5, 'python', '~/clara/dev/clara-python', True)

    tw.new_window(7, 'services', '~/clara/services')
    tw.new_window(9, 'log', '~/clara/services/log')

    tw.select_window(1)


if __name__ == '__main__':
    tw = TmuxWrapper('clara')
    if not tw.has_session():
        create_session(tw)
    rc = tw.attach()
    sys.exit(rc)
