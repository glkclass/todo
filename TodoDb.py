#      _____     _     __   _
#    /_  __/_ _/ /__ /   \/ /_
#     / / _ / _ / _ / /  / _ /
#    /_/___/___/___/___ /___/


import tinydb as db
import os
import path
from Scrpt import Scrpt


class TodoDb(Scrpt):
    """Provide database interface (TinyDB) for TODO project"""
    settings = {
        'path': {
            'plugin': 'Data/Packages/Todo',
            'todo.db': 'todo.json'
        },
    }

    def __init__(self, path2log=None, scrpt_settings={}, settings={}):
        """
        TodoDb constructor.

        Args:
        path2log, user_settings -- see 'Scrpt' class doc for details.
        settings -- todo_db settings

        Call superclass constructor, prepare parameters, open db .
        """
        Scrpt.__init__(self, path2log, scrpt_settings, settings)
        self.todo_db_fn = self.settings['path']['todo.db'] if path.isfile(self.settings['path']['todo.db']) else os.path.join(self.settings['path']['plugin'], self.settings['path']['todo.db'])
        self.todo_db_access('link')

    def todo_db_access(self, cmd):
        """Link/unlink todo database """
        if 'link' == cmd:
            self.todo_db = db.TinyDB(self.todo_db_fn, indent=2)
            self.todo_db_history = self.todo_db.table('todo_history')
            self.todo_db_sometime = self.todo_db.table('todo_sometime')
            self.todo_db_tomorrow = self.todo_db.table('todo_tomorrow')
            self.todo_db_holes = self.todo_db.table('todo_holes')
            self.todo_history_holes = self.todo_db_holes.get(db.Query()['year'] == 2017)
        elif 'unlink' == cmd:
            self.todo_db = None
            self.todo_db_history = None
            self.todo_db_sometime = None
            self.todo_db_tomorrow = None
            self.todo_db_holes = None
            self.todo_history_holes = None
        else:
            self.log.error('Wrong todo_db_access command: %s' % cmd)
    # ---------------------------------------------------------------------------------------------------------------------

    def main(self, **kwargs):
        # self.todo_db_access('link')
        return


if __name__ == "__main__":
    os.chdir('C:/avv/prtble/sublime_text')
    todo_db = TodoDb(settings={}).run()
