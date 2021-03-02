#      _____     _
#    /_  __/_ _/ /__
#     / / _ / _ / _ /
#    /_/___/___/___/

import sys
import os.path as osp
import subprocess


class TodoProxy(object):
    """Support TODO-table usage: window version"""
    settings = {
        'path': {
            'plugin': None,
            'todo.db': 'todo.json',
            'todo.pom': 'todo.pom',
            'main.sublime-menu': 'Main.sublime-menu',
            'main_base.sublime-menu': 'Main_base.sublime-menu',
        },
        'cache_size': 8,
        'todo_history': {'re': r'201\d/\d\d/\d\d', 'max_length': 0}
    }

    tbl = {
        'todo': {
            'doubleline': 80 * '=',
            'singleline': 80 * '-',
            'pointline': 80 * '.',

            'today': {
                'header': 'TODO Today:',
                'tbl_header': '|=EST=|=STA=|=POM=|=TASK=',
                'tbl_ph_line': '|' + 3 * ('     |') + ' ',
                'tbl_task_line': '|%s|%s|%s| %s',
                'add_task_line': ' / %s'},

            'sometime': {
                'header': 'TODO Sometime:',
                'tbl_header': '=DATE=        =TASK=',
                'update_line': '/ \n+ \n- ',
                'tbl_line': '%s    %s',
                'tomorrow_tag': 'todo tomorrow: '},

            'history': {
                'header': 'TODO History:'
            }
        },

        're': {
            'doubleline': r'==========+',
            'singleline': r'----------+',
            'pointline': r'\.\.\.\.\.\.\.\.\.\.+',

            'timestamp':
                {'header': r'(\d{4}/\d{2}/\d{2}), \w{3}, (\d{2}\:\d{2})'},

            'today': {
                'header': r'TODO Today:',
                'tbl_header': r'\|=EST=\|=STA=\|=POM=\|=TASK=',
                'tbl_task_line':
                    r'^ *\|+ *(\d*) *\|+ *([OoKk]*) *\|+ *(\d*) *\|+ *(.+)',
                'add_task_line': r'^ *(\d*) *\/ +(.+)$'},
            'sometime': {
                'header': r'TODO Sometime:',
                'tbl_header': r'=DATE=        =TASK=',
                'add_task_line': r'^ *([\+\-\/]) +(.+)$'},

            'history': {'header': r'TODO History:'},

        }
    }

    # ---------------------------------------------------------------------------------------------------------------------

    def __init__(self, settings={}):
        """
        Todo constructor.
        """
        # cwd = ".../prtble/sublime_text"
        self.settings['path']['plugin'] = osp.dirname(__file__)
        self.todo_pom = osp.join(
            self.settings['path']['plugin'], 
            self.settings['path']['todo.pom'])
        self.todo_db_fn = osp.join(
            self.settings['path']['plugin'], 
            self.settings['path']['todo.db'])
        self.todo_main_menu = osp.join(
            self.settings['path']['plugin'],
            self.settings['path']['main.sublime-menu'])
        self.todo_main_base_menu = osp.join(
            self.settings['path']['plugin'],
            self.settings['path']['main_base.sublime-menu'])

    def check_python_version(self):
        print(sys.version)
        print(sys.path)
        cmd = 'python -c "import sys; print(sys.version);" '
        version = subprocess.check_output(
            cmd, universal_newlines=True, timeout=1)
        print(version)

    def cmd(self, **kwargs):
        """ Proxy to call a function from todo module"""
        foo = 'cd %s & python -c "from todo import todo; todo.cmd(%s)"'
        str_args = ['%s=\\"%s\\"' % (key, val)
                    for key, val in kwargs.items() if str == type(val)]
        rest_args = ['%s=%s' % (key, val)
                     for key, val in kwargs.items() if str != type(val)]
        args = ', '.join(str_args + rest_args)
        res = subprocess.check_output(
            foo % (self.settings['path']['plugin'], args),
            shell=True, universal_newlines=True, timeout=10)
        print(res)
        return


if __name__ == "__main__":
    todo = TodoProxy().cmd(cmd_name="xxx", bar=2, foo=True)
    # todo = TodoProxy().check_python_version()

