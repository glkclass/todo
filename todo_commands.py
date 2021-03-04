#      _____     _
#    /_  __/_ _/ /__
#     / / _ / _ / _ /
#    /_/___/___/___/
import sys
import os.path as osp

import sublime
import sublime_plugin


todo = None


def plugin_loaded():
    """Called once by Sublime when plugin loaded"""

    # Combine and load settings
    settings = sublime.load_settings('Todo.sublime-settings')

    # add path to exteranl python 3.3 packages(tinydb, ...)
    pythonpath = settings.get('pythonpath', [])
    if pythonpath and list == type(pythonpath):
        for item in pythonpath:
            if item and str == type(item) and item not in sys.path:
                sys.path.insert(0, item.strip())

    todo_settings = settings.get('todo', {})  # extract todo settings
    todo_settings['path_todo_package'] = osp.dirname(__file__)  # set path to sublime package folder

    # add path to Todo python package: to access scrpt, ...
    todo_py3_package_path = osp.join(todo_settings['path_todo_package'], 'Todo')
    if todo_py3_package_path not in sys.path:
        sys.path.insert(0, todo_py3_package_path)

    # create Todo instance
    global todo
    from Todo.Todo import Todo
    todo = Todo.Todo(todo_settings)


class TodoTaskCmdCommand(sublime_plugin.WindowCommand):
    def run(self, cmd, task):
        todo.todo_task_cmd(cmd, task)
        sublime.status_message("Update task: %s -> %s" % (task, cmd))


class TodoTblNewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        todo.todo_tbl_new_cmd(show_todo_sometime, show_todo_history)
        sublime.active_window().open_file(todo.todo_pom)
        sublime.status_message("Empty TODO table was generated")


class TodoTblViewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        todo.todo_tbl_view_cmd(show_todo_sometime, show_todo_history)
        sublime.status_message("TODO table view")


class TodoDbUnlinkCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_db_unlink()
        sublime.status_message("TODO DB unlinked")


class TodoDbLinkCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_db_link()
        sublime.status_message("TODO DB linked")


class TodoTblOpenCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.active_window().open_file(todo.todo_pom)


class TodoInfoSaveCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_info_save_cmd()
        sublime.status_message("TODO info saved")


class TodoInfoUpdateCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        todo.todo_info_update_cmd()
        sublime.status_message("TODO info updated")
