import sublime
import sublime_plugin
import os
import sys


SETTINGS_FILE = 'Todo.sublime-settings'
settings = None
todo = None


def plugin_loaded():
    """Called once by Sublime when plugin loaded"""
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)
    todo_settings = settings.get('env').get(sys.platform).get('todo', settings.get("todo", {})) if settings.has('env') and sys.platform in settings.get('env') else settings.get("todo", {})
    pythonpath = settings.get('env').get(sys.platform).get('pythonpath', settings.get("pythonpath")) if settings.has('env') and sys.platform in settings.get('env') else settings.get("pythonpath")

    # update module search path
    if pythonpath:
        pythonpath = pythonpath.split(';')
        for item in pythonpath:
            if item not in sys.path:
                sys.path.insert(0, item.strip())

    global todo
    from Todo import Todo
    todo = Todo.Todo(todo_settings=todo_settings)


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
        todo.todo_info_save_cmd()
        sublime.status_message("TODO info saved")


class TodoInfoUpdateCommand(sublime_plugin.WindowCommand):
    def run(self):
        todo.todo_info_update_cmd()
        sublime.status_message("TODO info updated")
