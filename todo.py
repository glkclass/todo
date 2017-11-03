import re
from Scrpt import Scrpt
import tinydb as db
import operator
import os
import datetime

class Todo(Scrpt):
    """Support TODO-table usage"""
    param = {
                'todo.pom':                 'todo.pom',
                'todo.db':                  'todo.json',
                'todo.cache':               'todo_cache.json',
                'todo.sublime-menu':        'Main.sublime-menu',
                'todo_base.sublime-menu':   'Main_base.sublime-menu',
                'cache_size':               8,
                'todo_history':             {'re': '2017/\d\d/\d\d', 'max_length': 0}
            }

    tbl = {
            'todo_': {
                        'doubleline': 80 * '=',
                        'singleline': 80 * '-',
                        'pointline': 80 * '.',
                        'timestamp_header': '',
                        'today_header': 'TODO Today:',
                        'today_tbl_header': '|=EST=|=STA=|=POM=|=TASK=',
                        'today_ph_line': '|' + 3 * ('     |') + ' ',
                        'today_tbl_line': '|%s|%s|%s| %s',

                        'sometime_header': 'TODO Sometime:',
                        'sometime_tbl_header': '=DATE=        =TASK=',
                        'sometime_update_line': '/\n+\n-',
                        'sometime_tbl_line': '%s    %s',
                        'sometime_tomorrow_tag': 'todo tomorrow: ',

                        'history_tbl_header': 'TODO History:'
                    },

            're': {
                    'doubleline': r'=====+',
                    'singleline': r'-----+',

                    'timestamp_header': r'(\d{4}/\d{2}/\d{2}), \w{3}, (\d{2}\:\d{2})',

                    'today_header': r'TODO Today:',
                    'today_tbl_header': r'\|-EST-\|-STA-\|-POM-\|-TASK-',
                    'today_tbl_line': r'^[\| ]*(.*)\|+(.*)\|+(.*)\|+(.*)',

                    'sometime_header': r'TODO Sometime:',
                    'sometime_tbl_header': r'-DATE-        -TASK-',
                    'sometime_update_line': r'^ *([\+\-\/]) +(.*)$',

                    'history_tbl_header': r'TODO History:'
                  }
        }





    def __init__(self, path2log=None, user_settings={}, path2do_pom=None):
        """
        Todo constructor.

        Args:
        path2log, user_settings -- see 'Scrpt' class doc for details.
        self.todo_pom -- path to todo.pom file. Default value: param['path2do.pom']

        Call superclass constructor, prepare parameters, open db .
        """
        Scrpt.__init__(self, path2log, user_settings)
        self.holidays =  {
                        'Holidays': ['2017/01/01', '2017/01/07']
                    }

        self.todo_menu = os.path.join(path2do_pom, self.param['todo.sublime-menu']) if path2do_pom else self.param['todo.sublime-menu']
        self.todo_menu_base = os.path.join(path2do_pom, self.param['todo_base.sublime-menu']) if path2do_pom else self.param['todo_base.sublime-menu']
        self.todo_pom = os.path.join(path2do_pom, self.param['todo.pom']) if path2do_pom else self.param['todo.pom']
        self.todo_db = os.path.join(path2do_pom, self.param['todo.db']) if path2do_pom else self.param['todo.db']
        self.todo_cache = os.path.join(path2do_pom, self.param['todo.cache']) if path2do_pom else self.param['todo.cache']

        self.todo_db = db.TinyDB(self.todo_db, indent=2)
        self.todo_db_history = self.todo_db.table('todo_history')
        self.todo_db_sometime = self.todo_db.table('todo_sometime')
        self.todo_db_tomorrow = self.todo_db.table('todo_tomorrow')
        self.todo_db_holes = self.todo_db.table('todo_holes')
        self.todo_history_holes = self.todo_db_holes.get(db.Query()['year'] == 2017)

    def _get_timestamp(self):
        """Get current date/time stamp. Return dict with date/time values + date&time formatted strings."""
        foo = self.util.log.get_time()
        self.timestamp =    {   
                                'date': foo['date'],
                                'time': foo['time_wo_s'],
                            }
        return self.timestamp

    def _get_timestamp_header(self, date=None, time=None, time_evening=None):
        """Get formatted timestamp strings. Return dict with current week, day, ..."""
        if not date:
            timestamp = self._get_timestamp()
        else:
            timestamp = {'date': date, 'time': time}

        week = self.log.get_week(timestamp['date'])
        foo = {}
        foo['week'] = 'Week %02d' % week['num']

        if timestamp['time']:
            foo['day_time'] = '%s, %s, %s' % (timestamp['date'], week['day'], timestamp['time'])
        else:
            foo['day_time'] = 'Hole'

        foo['day'] = '%s, %s' % (timestamp['date'], week['day'])

        if time_evening:
            hm = [timestamp['time'].split(':'), time_evening.split(':')]
            hm = [[int(hm[i][j]) for j in (range(2))] for i in range(2)]
            duration_in_mins = (hm[1][0] - hm[0][0]) * 60 + (hm[1][1] - hm[0][1])
            duration_in_mins = duration_in_mins + 24 * 60 if duration_in_mins < 0 else duration_in_mins
            duration = '%02d:%02d' % (duration_in_mins / 60, duration_in_mins % 60)
            foo['day_time_delta'] = '%s, %s, %s - %s, %s' % (timestamp['date'], week['day'], timestamp['time'], time_evening, duration)
        else:
            foo['day_time_delta'] = 'Hole'

        return foo

    def _get_todo_today_placeholder(self, read4cache=False):
        """Generate TODO table part"""
        todo_today_buffer = []
        todo_today_buffer.append(self.tbl['todo_']['today_header'])
        todo_today_buffer.append(self.tbl['todo_']['doubleline'])
        todo_today_buffer.append(self.tbl['todo_']['today_tbl_header'])

        # extract&add planned tasks from db
        todo_tomorrow = self.todo_db_tomorrow.all()
        self.todo_db_tomorrow.purge()
        for item in todo_tomorrow:
            todo_today_buffer.append(self.tbl['todo_']['today_ph_line'] + item['task'])
        # add empty placeholders
        for i in range(10):
            todo_today_buffer.append(self.tbl['todo_']['today_ph_line'])
        todo_today_buffer.append(self.tbl['todo_']['singleline'])
        return todo_today_buffer

    def _get_todo_sometime(self):
        """Generate TODO table. History duration, stop date etc are defined by settings."""
        todo_sometime = self.todo_db_sometime.all()
        todo_sometime.sort(key=operator.itemgetter('date'))
        todo_sometime.reverse()
        todo_tomorrow = self.todo_db_tomorrow.all()

        todo_sometime_buffer = []
        todo_sometime_buffer.append(self.tbl['todo_']['sometime_header'])
        todo_sometime_buffer.append(self.tbl['todo_']['doubleline'])
        todo_sometime_buffer.append(self.tbl['todo_']['sometime_update_line'])
        todo_sometime_buffer.append(self.tbl['todo_']['sometime_tbl_header'])

        for item in todo_tomorrow:
            todo_sometime_buffer.append(self.tbl['todo_']['sometime_tbl_line'] % (item['date'], self.tbl['todo_']['sometime_tomorrow_tag'] + item['task']))

        for item in todo_sometime:
            todo_sometime_buffer.append(self.tbl['todo_']['sometime_tbl_line'] % (item['date'], item['task']))

        todo_sometime_buffer.append(self.tbl['todo_']['singleline'])
        return todo_sometime_buffer

    def _get_date_range(self, start_date, end_date):
        """Iterate dates from start_ to end_date"""
        start_date = [int(item) for item in start_date.split('/')]
        start_date = datetime.date(start_date[0], start_date[1], start_date[2])
        end_date = [int(item) for item in end_date.split('/')]
        end_date = datetime.date(end_date[0], end_date[1], end_date[2])
        delta = datetime.timedelta(days=1)
        end_date -= delta
        missed_range = []
        while start_date < end_date:
            missed_range.append(end_date.strftime('%Y/%m/%d'))
            end_date -= delta
        return missed_range

    def _get_todo_history_holes(self, date_range, week_pre):
        history_buffer = []
        for item in date_range:
            week = self.log.get_week(item)
            if week_pre != week['num']:
                headers = self._get_timestamp_header(item)
                history_buffer.extend(['', headers['week'], self.tbl['todo_']['singleline']])
            if week['day'] in ('Sat', 'Sun'):
                history_buffer.append('  %s    Weekend' % self._get_timestamp_header(item)['day'])
            elif item in self.todo_history_holes['Holidays']:
                history_buffer.append('  %s    Holiday' % self._get_timestamp_header(item)['day'])
            elif item in self.todo_history_holes['Vacation']:
                history_buffer.append('  %s    Vacation' % self._get_timestamp_header(item)['day'])
            elif item in self.todo_history_holes['Sick']:
                history_buffer.append('  %s    Sick dayoff' % self._get_timestamp_header(item)['day'])
            else:
                history_buffer.append('  %s    Missed' % self._get_timestamp_header(item)['day'])
            week_pre = week['num']
        # self.info (history_buffer)
        return history_buffer, week_pre

    def _get_todo_history(self):
        """Generate history part of TODO table. History duration, stop date etc are defined by settings."""
        todo_history = self.todo_db_history.search((db.Query().date.search(self.param['todo_history']['re'])))
        todo_history.sort(key=operator.itemgetter('date'))
        todo_history.reverse()
        # self.log.info(todo_history)
        todo_history_buffer = []
        todo_history_buffer.append(self.tbl['todo_']['history_tbl_header'])
        todo_history_buffer.append(self.tbl['todo_']['doubleline'])
        # todo_history_buffer.append('')

        week_pre = -1
        day_pre = self._get_timestamp()['date']
        for day in todo_history:
            # fill todo_history holes: weekends, holidays, vacations, etc
            missed_range = self._get_date_range(day['date'], day_pre)
            if missed_range:
                todo_history_buffer.append('')
                history_buffer, week_pre = self._get_todo_history_holes(missed_range, week_pre)
                todo_history_buffer.extend(history_buffer)

            week_cur = self.log.get_week(day['date'])['num']
            headers = self._get_timestamp_header(day['date'], day['time_morning'], day['time_evening'])
            if week_pre != week_cur:
                todo_history_buffer.extend(['', headers['week'], self.tbl['todo_']['singleline']])

            todo_history_buffer.append('')
            todo_history_buffer.append('  %s' % headers['day_time_delta'])
            todo_history_buffer.append('    %s' % self.tbl['todo_']['today_tbl_header'])
            total = {'est': 0, 'pom': 0}
            for item in day['todo_item']:
                today_tbl_line = (  self.util.allign_text(str(item['est']), 5,),
                                    self.util.allign_text({0: '', 1: 'Ok'}[item['sta']], 5),
                                    self.util.allign_text(str(item['pom']), 5),
                                    item['task'])
                todo_history_buffer.append('    ' + self.tbl['todo_']['today_tbl_line'] % today_tbl_line)
                total['est'] += item['est']
                total['pom'] += item['pom']
            today_tbl_line = (  self.util.allign_text(str(total['est']), 5, alligner='-'),
                                self.util.allign_text('', 5, alligner='-'),
                                self.util.allign_text(str(total['pom']), 5, alligner='-'),
                                '=Total')
            todo_history_buffer.append('    ' + self.tbl['todo_']['today_tbl_line'] % today_tbl_line)

            week_pre = week_cur
            day_pre = day['date']
        todo_history_buffer.append(self.tbl['todo_']['pointline'])
        return todo_history_buffer






    def _extract_todo_tbl_buffer(self, todo_pom_buffer):
        """
        Extract TODO tables content bounded by start/stop markers from todo.pom txt buffer

        Args: todo_pom_buffer -- todo.pom content (lines)
    
        Parse todo.pom lines, split timestamp & today/sometime tables into separate line buffers
        """

        # self.info(todo_pom_buffer)
        todo_buffer = {'timestamp': [], 'today': [], 'sometime': [], 'history': []}

        start = 0
        end = len(todo_pom_buffer)
        for i in (start, end):
            line = todo_pom_buffer[i]
            if re.search(self.tbl['re']['timestamp_header'], line):
                todo_buffer['timestamp'].append(line)
                break

        todo_buffer_act = None
        start = i + 1
        for i in range(start, end):
            line = todo_pom_buffer[i]
            todo_today_header = re.search(self.tbl['re']['today_header'], line)
            if todo_today_header is None:
                if todo_buffer_act is not None:
                    todo_buffer_act.append(line)
                    if re.search(self.tbl['re']['singleline'], line):
                        todo_buffer_act = None
                        break
            else:
                todo_buffer_act = todo_buffer['today']
                todo_buffer_act.append(line)

        for j in range(2):
            start = i + 1
            for i in range(start, end):
                line = todo_pom_buffer[i]
                todo_sometime_header = re.search(self.tbl['re']['sometime_header'], line)
                todo_history_header = re.search(self.tbl['re']['history_tbl_header'], line)

                if todo_sometime_header is None and todo_history_header is None:
                    if todo_buffer_act is not None:
                        todo_buffer_act.append(line)
                        if re.search(self.tbl['re']['singleline'], line):
                            todo_buffer_act = None
                            break
                else:
                    if todo_sometime_header is not None:
                        todo_buffer_act = todo_buffer['sometime']
                        todo_buffer_act.append(line)
                    elif todo_history_header is not None:
                        todo_buffer['history'].append(line)
                        i = end - 1
                        break
        # self.info(todo_buffer)
        return todo_buffer

    def _parse_todo_today_content(self, todo_today_line):
        """Parse TODO today table line components"""
        foo = []
        for item in todo_today_line:
            if item['task'] and '=TASK=' != item['task']:
                if '' == item['est']:
                    est = 0
                else:
                    est = re.search(r"(\d+)", item['est'])
                    est = int(est.group(1)) if est else 0

                sta = re.search(r"[Oo][Kk]", item['sta'])
                sta = 1 if sta else 0

                if '' == item['pom']:
                    pom = 0
                else:
                    pom = re.search(r"(\d+)", item['pom'])
                    pom = int(pom.group(1)) if pom else 0
                foo.append({'est': est, 'sta': sta, 'pom': pom, 'task': item['task']})
        return foo

    def _extract_todo_tbl_info(self, todo_buffer):
        """
        Extract TODO info (timestamp, TODO today tasks&est&pom&sts, TODO sometime tasks) from TODO table

        Args: todo_buffer -- dict containing 3 line(string) buffers: timestamp, TODO today/sometime tables

        Extract table content from appropriate buffers, parse it and store.
        """

        todo_info = {}
        for line in todo_buffer['timestamp']:
            timestamp_header = re.search(self.tbl['re']['timestamp_header'], line)  # find timestamp header
            if timestamp_header:
                todo_info['date'] = timestamp_header.group(1)
                todo_info['time'] = timestamp_header.group(2)
                break

        foo = []
        for line in todo_buffer['today']:
            today_tbl_line = re.search(self.tbl['re']['today_tbl_line'], line)
            if today_tbl_line:
                foo.append({'est': today_tbl_line.group(1).strip(), 'sta': today_tbl_line.group(2).strip(), 'pom': today_tbl_line.group(3).strip(), 'task': today_tbl_line.group(4).strip()})

        todo_info['today'] = self._parse_todo_today_content(foo)

        todo_info['sometime'] = {'+': [], '-': [], '/': []}
        for line in todo_buffer['sometime']:
            sometime_tbl_line = re.search(self.tbl['re']['sometime_update_line'], line)
            if sometime_tbl_line:
                todo_info['sometime'][sometime_tbl_line.group(1)].append(sometime_tbl_line.group(2).strip())

        return todo_info

    def _extract_todo_info(self):
        """Read todo.pom and extract todo info (timestamp, shortterm tasks&est&pom&sta, sometime todo)"""
        todo_pom_buffer = self.util.file.load(self.todo_pom, 'txt', rstrip='\n')
        todo_buffer = self._extract_todo_tbl_buffer(todo_pom_buffer)
        todo_info = self._extract_todo_tbl_info(todo_buffer)

        if not todo_buffer or not todo_info:
            self.log.error('TODO table info wasn\'t found!')
            return {'todo_date': None, 'todo_tbl': None, 'todo_info': None}
        else:
            return {'tbl_buffer': todo_buffer, 'info': todo_info}

    def _history_update(self, todo):
        """Update history db item with extracted todo info"""
        foo = todo['info']['today']
        bar = self.todo_db_history.get(db.Query().date == todo['info']['date'])['todo_item']
        for item_foo in foo:
            for item_bar in bar:
                if item_foo['task'] == item_bar['task']:
                    # update existing task
                    item_bar['est'] = item_foo['est']
                    item_bar['sta'] = item_foo['sta']
                    item_bar['pom'] += item_foo['pom']
                    break
            else:
                if 0 != item_foo['pom']:
                    bar.append(item_foo)  # add new task

        self.todo_db_history.update({'todo_item': bar, 'time_evening': self._get_timestamp()['time']}, db.Query().date == todo['info']['date'])
        return

    def _todo_info_save(self, todo):
        """Save extracted todo info to history db"""

        # todo today
        if (self.todo_db_history.contains(db.Query().date == todo['info']['date'])):
            self._history_update(todo)
        else:
            todo_item_completed = [item for item in todo['info']['today'] if item['pom'] != 0]
            bar = {'date': todo['info']['date'], 'time_morning': todo['info']['time'], 'time_evening': self._get_timestamp()['time'], 'todo_item': todo_item_completed}
            self.todo_db_history.insert(bar)

        # todo sometime
        for item in todo['info']['sometime']['+']:
            if not self.todo_db_sometime.contains(db.Query().task == item):
                self.todo_db_sometime.insert({'task': item, 'date': todo['info']['date']})

        for item in todo['info']['sometime']['-']:
            self.todo_db_sometime.remove(db.Query().task == item)
            self.todo_db_tomorrow.remove(db.Query().task == item.replace(self.tbl['todo_']['sometime_tomorrow_tag'], ''))

        for item in todo['info']['sometime']['/']:
            if '' != item:
                if not self.todo_db_tomorrow.contains(db.Query().task == item):
                    self.todo_db_tomorrow.insert({'task': item, 'date': todo['info']['date']})

    def _get_todo_today(self, todo):
        """Generate TODO today table with current tasks (with zeroed 'pom' fileds of just saved tasks) from todo.pom"""
        todo_today_buffer = []
        todo_today_buffer.append(self.tbl['todo_']['today_header'])
        todo_today_buffer.append(self.tbl['todo_']['doubleline'])
        todo_today_buffer.append(self.tbl['todo_']['today_tbl_header'])

        # add current tasks (just saved tasks with zeroed 'pom' field)
        for item in todo['info']['today']:
            est = '' if 0 == item['est'] else str(item['est'])
            today_tbl_line = (  self.util.allign_text(est, 5,),
                                self.util.allign_text({0: '', 1: 'Ok'}[item['sta']], 5),
                                self.util.allign_text('', 5),
                                item['task'])
            todo_today_buffer.append(self.tbl['todo_']['today_tbl_line'] % today_tbl_line)

        # add empty placeholders
        for i in range(5):
            todo_today_buffer.append(self.tbl['todo_']['today_ph_line'])
        todo_today_buffer.append(self.tbl['todo_']['singleline'])
        return todo_today_buffer

# API methods
    def todo_tbl_new(self, show_todo_sometime=False, show_todo_history=False):
        """
        Generate TODO tables and save them to todo.pom

        Args:
        show_todo_sometime -- turn on/off TODO sometime table printing

        Generate empty TODO today, history and maybe sometime tables
        """
        todo_tbl = []
        todo_tbl.append(self._get_timestamp_header()['day_time'])
        todo_tbl.append('')
        todo_tbl += self._get_todo_today_placeholder(False)
        todo_tbl.append('')
        if show_todo_sometime:
            todo_tbl += self._get_todo_sometime()
            todo_tbl.append('')
        if show_todo_history:
            todo_tbl += self._get_todo_history()
        self.util.file.save(todo_tbl, self.todo_pom, 'txt', eol='\n')

    def todo_tbl_save(self):
        """Extract todo info from todo.pom and save it to db. Regenerate todo.pom with updated history"""
        todo = self._extract_todo_info()
        self._todo_info_save(todo)
        todo_sometime_tbl = self._get_todo_sometime() + [''] if todo['tbl_buffer']['sometime'] else []
        todo_history_tbl = self._get_todo_history() if todo['tbl_buffer']['history'] else []
        # self.util.path.remove(self.todo_pom)
        self.util.file.save(todo['tbl_buffer']['timestamp'] + [''] + self._get_todo_today(todo) + [''] + todo_sometime_tbl + todo_history_tbl, self.todo_pom, 'txt', eol='\n')

    def todo_tbl_view(self, show_todo_sometime=False, show_todo_history=False):
        """
        Regenerate todo.pom with given settings

        Args:   show_todo_sometime - add todo sometime tbl to todo.pom
                show_todo_history - add todo history tbl to todo.pom
`
        TODO timestamp and TODO today must be present, TODO sometime & history - optional
        """
        todo = self._extract_todo_info()
        todo_sometime_tbl = self._get_todo_sometime() + [''] if show_todo_sometime else []
        todo_history_tbl = self._get_todo_history() if show_todo_history else []
        self.util.file.save(todo['tbl_buffer']['timestamp'] + [''] + todo['tbl_buffer']['today'] + [''] + todo_sometime_tbl + todo_history_tbl, self.todo_pom, 'txt', eol='\n')


    def _update_todo_menu(self):
        todo = self._extract_todo_info()
        tasks = [item['task'] for item in todo['info']['today']]
        todo_menu_base = self.util.file.load(self.todo_menu_base, 'json')

        children = []
        for task in tasks:
            bar =   {
                        "caption": task,
                        "children":
                        [
                            {"caption": "Short break",  "command": "todo_menu_cmd", "id": "todo_menu_short_break",  "args": {"task": task, "cmd": "short_break"}},
                            {"caption": "Long break",   "command": "todo_menu_cmd", "id": "todo_menu_long_break",   "args": {"task": task, "cmd": "long_break"}},
                            {"caption": "Ok",           "command": "todo_menu_cmd", "id": "todo_menu_ok",           "args": {"task": task, "cmd": "ok"}}
                        ]
                    }
            children.append(bar)
        tasks_menu = {"caption": "Tasks", 'children': children}
        todo_menu_base[0]['children'].append(tasks_menu)

        self.util.file.save(todo_menu_base, self.todo_menu, 'json')
        return

    def todo_menu_cmd(self, cmd, task):
        self.info(cmd)
        self.info(task)
        return

    def main(self, **kwargs):
        # self.todo_tbl_new(True, True)
        # self.todo_tbl_view(True, True)
        # self.todo_tbl_save()
        # self.todo_db_holes.purge()
        # self.todo_db_holes.insert({'year': 2017, 'Holidays': ['2017/10/14'], 'Vacation': ['2017/10/10'], 'Sick': ['2017/10/03']})
        self._update_todo_menu()



        return

if __name__ == "__main__":
    Todo().run()



















































    # def _save_todo_cache(self, foo):
    #     """Save current TODO table content to cache"""
    #     if len(foo) > 2:  # check the TODO table was really found & extracted
    #         if self.util.path.exists(self.todo_cache):
    #             todo_cache = self.util.file.load(self.todo_cache, 'json')
    #             if len(todo_cache) >= self.param['cache_size'] :
    #                 todo_cache.pop(-1)
    #             todo_cache.insert(0, foo)
    #             self.util.file.save(todo_cache, self.todo_cache, 'json')
    #         else:
    #             self.util.file.save([foo], self.todo_cache, 'json')
