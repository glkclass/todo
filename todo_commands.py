import sublime
import sublime_plugin
# import os
import sys


SETTINGS_FILE = 'Todo.sublime-settings'
settings = None
todo = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)

    # update module search path
    pythonpath = settings.get("PYTHONPATH")
    # pythonpath = os.environ[PYTHONPATH'']
    if pythonpath:
        pythonpath = pythonpath.split(';')
        for item in pythonpath:
            if item not in sys.path:
                sys.path.append(item)

    global todo
    from Todo import Todo
    todo = Todo.Todo(path2do_pom=settings.get('path2do_pom'))


class TodoMenuCmdCommand(sublime_plugin.WindowCommand):
    def run(self, cmd, task):
        todo.todo_menu_cmd(cmd, task)
        sublime.status_message("Update task %s: %s" % (task, cmd))


class TodoTblNewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        todo.todo_tbl_new(show_todo_sometime, show_todo_history)
        sublime.active_window().open_file(todo.todo_pom)
        sublime.status_message("Empty TODO table was generated")


class TodoTblViewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        todo.todo_tbl_view(show_todo_sometime, show_todo_history)
        sublime.status_message("TODO table view")


class TodoTblSaveCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_tbl_save()
        sublime.status_message("TODO table was saved")


class TodoTblOpenCommand(sublime_plugin.WindowCommand):
    def run(self, file):
        sublime.active_window().open_file(todo.todo_pom)


class TodoTblTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        return
        # print(settings.get("path2do_pom"))
        # print(sys.version)
        # print(sys.path)
