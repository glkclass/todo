#      _____     _
#    /_  __/_ _/ /__
#     / / _ / _ / _ /
#    /_/___/___/___/

import sublime
import sublime_plugin

from Todo import TodoProxy

todo_proxy = None


def plugin_loaded():
    """Called once by Sublime when plugin loaded"""

    # Combine and load settings
    settings = sublime.load_settings('Todo.sublime-settings')

    # create Todo instance
    global todo_proxy
    todo_proxy = TodoProxy.TodoProxy(
        settings=settings.get('todo_settings', {}))


class TodoTaskCmdCommand(sublime_plugin.WindowCommand):
    def run(self, cmd, task):
        todo_proxy.todo_task_cmd(cmd, task)
        todo_proxy.cmd(
            cmd_name='todo_task_cmd',
            cmd=cmd,
            task=task)
        sublime.status_message("Update task: %s -> %s" % (task, cmd))


class TodoTblNewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        # todo_proxy.todo_tbl_new_cmd(show_todo_sometime, show_todo_history)
        todo_proxy.cmd(
            cmd_name='todo_tbl_new_cmd',
            show_todo_sometime=show_todo_sometime,
            show_todo_history=show_todo_history)
        sublime.active_window().open_file(todo_proxy.todo_pom)
        sublime.status_message("Empty TODO table was generated")


class TodoTblViewCommand(sublime_plugin.WindowCommand):
    def run(self, show_todo_sometime=False, show_todo_history=False):
        # todo_proxy.todo_tbl_view_cmd(show_todo_sometime, show_todo_history)
        todo_proxy.cmd(
            cmd_name='todo_tbl_view_cmd',
            show_todo_sometime=show_todo_sometime,
            show_todo_history=show_todo_history)
        sublime.status_message("TODO table view")


class TodoDbUnlinkCommand(sublime_plugin.WindowCommand):
    def run(self):
        # todo_proxy.todo_db_access('unlink')
        todo_proxy.cmd(cmd_name='todo_db_access', cmd='unlink')
        sublime.status_message("TODO DB unlinked")


class TodoDbLinkCommand(sublime_plugin.WindowCommand):
    def run(self):
        # todo_proxy.todo_db_access('link')
        todo_proxy.cmd(cmd_name='todo_db_access', cmd='link')
        sublime.status_message("TODO DB linked")


class TodoTblOpenCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.active_window().open_file(todo_proxy.todo_pom)


class TodoInfoSaveCommand(sublime_plugin.WindowCommand):
    def run(self):
        # todo_proxy.todo_info_save_cmd()
        todo_proxy.cmd(cmd_name='todo_info_save_cmd')
        sublime.status_message("TODO info saved")


class TodoInfoUpdateCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        # todo_proxy.todo_info_update_cmd()
        todo_proxy.cmd(cmd_name='todo_info_update_cmd')
        sublime.status_message("TODO info updated")
