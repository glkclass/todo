import sublime
import sublime_plugin
import os
import sys


SETTINGS_FILE = 'Todo.sublime-settings'
settings = None
todo = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)

    if settings.has("env"):
        todo_settings = settings.get("env")[sys.platform]['todo']
        pythonpath = settings.get("env")[sys.platform]['pythonpath']
    else:
        todo_settings = settings.get("todo")
        pythonpath = settings.get("pythonpath")

    # update module search path
    # pythonpath = os.environ[PYTHONPATH'']
    if pythonpath:
        pythonpath = pythonpath.split(';')
        for item in pythonpath:
            if item not in sys.path:
                sys.path.append(item)

    global todo
    from Todo import Todo
    todo = Todo.Todo(todo_settings=todo_settings)


class TodoMenuCmdCommand(sublime_plugin.WindowCommand):
    def run(self, cmd, task):
        todo.todo_menu_cmd(cmd, task)
        sublime.status_message("Update task: %s -> %s" % (task, cmd))


class TodoTblNewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        todo.todo_tbl_new(show_todo_sometime, show_todo_history)
        sublime.active_window().open_file(todo.todo_pom)
        sublime.status_message("Empty TODO table was generated")


class TodoTblViewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        todo.todo_tbl_view(show_todo_sometime, show_todo_history)
        sublime.status_message("TODO table view")


class TodoDbUnlinkCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_db_access('unlink')
        sublime.status_message("TODO DB unlinked")


class TodoDbLinkCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_db_access('link')
        sublime.status_message("TODO DB linked")


class TodoTblOpenCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.active_window().open_file(todo.todo_pom)


class TodoInfoSaveCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_info_save()
        sublime.status_message("TODO info saved")


class TodoInfoUpdateCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_info_update()
        sublime.status_message("TODO info updated")
