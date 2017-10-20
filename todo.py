import sublime
import sublime_plugin

SETTINGS_FILE = 'Todo.sublime-settings'
settings = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)


class TodoTblTestCommand(sublime_plugin.TextCommand):
    def run(self, edit, file):
        print(settings.get("todo_pom"))


class TodoTblNewCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class TodoTblSaveCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class TodoTblOpenCommand(sublime_plugin.WindowCommand):
    def run(self, file):
        sublime.active_window().open_file(settings.get('todo_pom'))
