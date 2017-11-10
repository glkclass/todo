import re
import tinydb as db
import operator
import os
import datetime

from Scrpt import Scrpt



class Todo_window(Scrpt):
    """Support TODO-table usage: window version"""
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
            'todo': {
                        'doubleline': 80 * '=',
                        'singleline': 80 * '-',
                        'pointline': 80 * '.',


                        'today':    {
                                        'header': 'TODO Today:',
                                        'tbl_header': '|=EST=|=STA=|=POM=|=TASK=',
                                        'tbl_ph_line': '|' + 3 * ('     |') + ' ',
                                        'tbl_task_line': '|%s|%s|%s| %s',
                                        'add_task_line': ' / %s',
                                    },

                        'sometime': {                    
                                        'header': 'TODO Sometime:',
                                        'tbl_header': '=DATE=        =TASK=',
                                        'update_line': '/\n+\n-',
                                        'tbl_line': '%s    %s',
                                        'tomorrow_tag': 'todo tomorrow: ',
                                    },

                        'history':  {
                                        'header': 'TODO History:'
                                    }
                    },

            're': {
                    'doubleline': r'=====+',
                    'singleline': r'-----+',
                    'pointline': r'\.\.\.\.\.+',

                    'timestamp': {'header': r'(\d{4}/\d{2}/\d{2}), \w{3}, (\d{2}\:\d{2})'},

                    'today': {
                                'header': r'TODO Today:',
                                'tbl_header': r'\|=EST=\|=STA=\|=POM=\|=TASK=',
                                'tbl_task_line': r'^ *\|+ *(\d*) *\|+ *([OoKk]*) *\|+ *(\d*) *\|+ *([^ ]+)',
                                'add_task_line': r'^ *(\d*) *\/ +([^ ]+)$'
                            },

                    'sometime': {                    
                                    'header': r'TODO Sometime:',
                                    'tbl_header': r'=DATE=        =TASK=',
                                    'add_task_line': r'^ *([\+\-\/]) +(.+)$',
                                },

                    'history': {'header': r'TODO History:'},

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

        self.todo_pom = os.path.join(path2do_pom, 'todo_.pom') if path2do_pom else 'todo_.pom'
        self.todo_db = os.path.join(path2do_pom, self.param['todo.db']) if path2do_pom else self.param['todo.db']
        self.todo_cache = os.path.join(path2do_pom, self.param['todo.cache']) if path2do_pom else self.param['todo.cache']
        self.todo_menu = os.path.join(path2do_pom, self.param['todo.sublime-menu']) if path2do_pom else self.param['todo.sublime-menu']
        self.todo_menu_base = os.path.join(path2do_pom, self.param['todo_base.sublime-menu']) if path2do_pom else self.param['todo_base.sublime-menu']

        self.todo_db = db.TinyDB(self.todo_db, indent=2)
        self.todo_db_history = self.todo_db.table('todo_history')
        self.todo_db_sometime = self.todo_db.table('todo_sometime')
        self.todo_db_tomorrow = self.todo_db.table('todo_tomorrow')
        self.todo_db_holes = self.todo_db.table('todo_holes')
        self.todo_history_holes = self.todo_db_holes.get(db.Query()['year'] == 2017)

# ---------------------------------------------------------------------------------------------------------------------

    def _get_timestamp(self):
        """Get current date/time stamp. Return dict with date/time values + date&time formatted strings."""
        foo = self.util.log.get_time()
        self.timestamp =    {   
                                'date': foo['date'],
                                'time': foo['time_wo_s'],
                            }
        return self.timestamp

    def _generate_timestamp_header(self, date=None, time=None, time_evening=None):
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

    def _generate_todo_today(self, pending_tasks=[], tasks4tbl=[]):
        """Generate TODO today table part"""
        n_add_task_line = 7 if not pending_tasks and not tasks4tbl else (5 if not tasks4tbl else 3)
        todo_today_buffer = []
        todo_today_buffer.append(self.tbl['todo']['today']['header'])
        todo_today_buffer.append(self.tbl['todo']['doubleline'])
        if pending_tasks:
            pending_tasks = [self.tbl['todo']['today']['add_task_line'] % item for item in pending_tasks]
            todo_today_buffer.extend(pending_tasks)
        todo_today_buffer.extend(n_add_task_line * [self.tbl['todo']['today']['add_task_line'] % ''])

        todo_today_buffer.append(self.tbl['todo']['today']['tbl_header'])
        if tasks4tbl:
            for item in tasks4tbl:
                est = str(item['est']) if 0 != item['est'] else ''
                pom = str(item['pom']) if 0 != item['pom'] else ''
                todo_today_tbl_line = ( self.util.allign_text(est, 5,),
                                        self.util.allign_text({0: '', 1: 'Ok'}[item['sta']], 5),
                                        self.util.allign_text(pom, 5),
                                        item['task'])
                todo_today_buffer.append(self.tbl['todo']['today']['tbl_task_line'] % todo_today_tbl_line)
        else:
            todo_today_buffer.append(self.tbl['todo']['today']['tbl_ph_line'])        
        todo_today_buffer.append(self.tbl['todo']['singleline'])
        return todo_today_buffer

    def _generate_todo_sometime(self):
        """Generate TODO table. History duration, stop date etc are defined by settings."""
        todo_sometime = self.todo_db_sometime.all()
        todo_sometime.sort(key=operator.itemgetter('date'))
        todo_sometime.reverse()
        todo_tomorrow = self.todo_db_tomorrow.all()

        todo_sometime_buffer = []
        todo_sometime_buffer.append(self.tbl['todo']['sometime']['header'])
        todo_sometime_buffer.append(self.tbl['todo']['doubleline'])
        todo_sometime_buffer.append(self.tbl['todo']['sometime']['update_line'])
        todo_sometime_buffer.append(self.tbl['todo']['sometime']['tbl_header'])

        for item in todo_tomorrow:
            todo_sometime_buffer.append(self.tbl['todo']['sometime']['tbl_line'] % (item['date'], self.tbl['todo']['sometime']['tomorrow_tag'] + item['task']))

        for item in todo_sometime:
            todo_sometime_buffer.append(self.tbl['todo']['sometime']['tbl_line'] % (item['date'], item['task']))

        todo_sometime_buffer.append(self.tbl['todo']['singleline'])
        return todo_sometime_buffer

    def _get_date_range(self, start_date, end_date):
        """Iterate dates from start_ to end_date"""
        start_date = [int(item) for item in start_date.split('/')]
        start_date = datetime.date(start_date[0], start_date[1], start_date[2])
        end_date = [int(item) for item in end_date.split('/')]
        end_date = datetime.date(end_date[0], end_date[1], end_date[2])
        delta = datetime.timedelta(days=1)
        end_date -= delta
        date_range = []
        while start_date < end_date:
            date_range.append(end_date.strftime('%Y/%m/%d'))
            end_date -= delta
        return date_range

    def _get_todo_history_holes(self, date_range, week_pre):
        history_buffer = []
        for item in date_range:
            week = self.log.get_week(item)
            if week_pre != week['num']:
                headers = self._generate_timestamp_header(item)
                history_buffer.extend(['', headers['week'], self.tbl['todo']['singleline']])
            if week['day'] in ('Sat', 'Sun'):
                history_buffer.append('  %s    Weekend' % self._generate_timestamp_header(item)['day'])
            elif item in self.todo_history_holes['Holidays']:
                history_buffer.append('  %s    Holiday' % self._generate_timestamp_header(item)['day'])
            elif item in self.todo_history_holes['Vacation']:
                history_buffer.append('  %s    Vacation' % self._generate_timestamp_header(item)['day'])
            elif item in self.todo_history_holes['Sick']:
                history_buffer.append('  %s    Sick dayoff' % self._generate_timestamp_header(item)['day'])
            else:
                history_buffer.append('  %s    Missed' % self._generate_timestamp_header(item)['day'])
            week_pre = week['num']
        # self.info (history_buffer)
        return history_buffer, week_pre

    def _generate_todo_history(self):
        """Generate history part of TODO table. History duration, stop date etc are defined by settings."""
        todo_history = self.todo_db_history.search((db.Query().date.search(self.param['todo_history']['re'])))
        todo_history.sort(key=operator.itemgetter('date'))
        todo_history.reverse()
        # self.log.info(todo_history)
        todo_history_buffer = []
        todo_history_buffer.append(self.tbl['todo']['history']['header'])
        todo_history_buffer.append(self.tbl['todo']['doubleline'])
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
            headers = self._generate_timestamp_header(day['date'], day['time_morning'], day['time_evening'])
            if week_pre != week_cur:
                todo_history_buffer.extend(['', headers['week'], self.tbl['todo']['singleline']])

            todo_history_buffer.append('')
            todo_history_buffer.append('  %s' % headers['day_time_delta'])
            todo_history_buffer.append('    %s' % self.tbl['todo']['today']['tbl_header'])
            total = {'est': 0, 'pom': 0}
            for item in day['todo_item']:
                today_tbl_line = (  self.util.allign_text(str(item['est']), 5,),
                                    self.util.allign_text({0: '', 1: 'Ok'}[item['sta']], 5),
                                    self.util.allign_text(str(item['pom']), 5),
                                    item['task'])
                todo_history_buffer.append('    ' + self.tbl['todo']['today']['tbl_task_line'] % today_tbl_line)
                total['est'] += item['est']
                total['pom'] += item['pom']
            today_tbl_line = (  self.util.allign_text(str(total['est']), 5, alligner='-'),
                                self.util.allign_text('', 5, alligner='-'),
                                self.util.allign_text(str(total['pom']), 5, alligner='-'),
                                '=Total')
            todo_history_buffer.append('    ' + self.tbl['todo']['today']['tbl_task_line'] % today_tbl_line)

            week_pre = week_cur
            day_pre = day['date']
        todo_history_buffer.append(self.tbl['todo']['pointline'])
        return todo_history_buffer

# ---------------------------------------------------------------------------------------------------------------------

    def _extract_tbl_buffer(self, line_buffer, header):
        """
        Extract TODO table content bounded by start/stop markers from txt buffer

        Args:   line_buffer     -- ['xxx', 'yyy', ...] -- buffer containing txt lines
                header          -- {'start': 'start_marker', 'stop': 'stop_marker'} -- start/stop markers

        Read line_buffer, extract timestamp/today/sometime/history table into separate txt line buffer without any parsing
        """

        # self.info(line_buffer)
        start = 0
        end = len(line_buffer)
        tbl_buffer = []
        buffer_act = False
        marker = header['start']
        for i in range(start, end):
            line = line_buffer[i]
            marker_found = re.search(marker, line)
            if marker_found is None:
                if buffer_act:
                    tbl_buffer.append(line)
            else:
                if marker is header['start']:
                    buffer_act = True
                    tbl_buffer.append(line)
                    marker = header['stop']
                    if '' == marker:
                        break  # (stop marker == '') => tbl_buffer contains only start header
                else:  # stop marker found
                    tbl_buffer.append(line)
                    break
        else:
            self.error('Table buffer start/stop header wasn\'t found: %s or %s' % (header['start'], header['stop']))
        return i, tbl_buffer

    def _extract_todo_tbl_buffers(self, todo_pom_buffer, extract_history=False):
        """
        Extract TODO tables content bounded by start/stop markers from todo.pom txt buffer

        Args:   todo_pom_buffer     -- todo.pom content (lines)
                extract_history     -- whether extract history buufer or no

        Read todo.pom txt lines, extract timestamp + today + sometime + history tables into separate txt line buffers without any further parsing
        """

        # self.info(todo_pom_buffer)
        todo_buffers = {'timestamp': None, 'today': None, 'sometime': None, 'history': None}
        i, todo_buffers['timestamp'] = self._extract_tbl_buffer(todo_pom_buffer, {'start': self.tbl['re']['timestamp']['header'], 'stop': ''})
        i, todo_buffers['today'] = self._extract_tbl_buffer(todo_pom_buffer[i:], {'start': self.tbl['re']['today']['header'], 'stop': self.tbl['re']['singleline']})
        _, todo_buffers['sometime'] = self._extract_tbl_buffer(todo_pom_buffer[i:], {'start': self.tbl['re']['sometime']['header'], 'stop': self.tbl['re']['singleline']})
        if extract_history:
            _, todo_buffers['history'] = self._extract_tbl_buffer(todo_pom_buffer[i:], {'start': self.tbl['re']['history']['header'], 'stop': self.tbl['re']['pointline']})
        # self.info(todo_buffers['timestamp'])
        # self.info(todo_buffers['today'])
        # self.info(todo_buffers['sometime'])
        # self.info(todo_buffers['history'])
        return todo_buffers

# ---------------------------------------------------------------------------------------------------------------------

    def _parse_timestamp_header(self, line_buffer):
        """Find today timestamp line, extract and store date/time"""
        for line in line_buffer:
            timestamp_header = re.search(self.tbl['re']['timestamp']['header'], line)
            if timestamp_header:
                date_ = timestamp_header.group(1)
                time_ = timestamp_header.group(2)
                return date_, time_
        self.error('Today timestamp header wasn\'t found')
        return None, None

    def _parse_todo_today(self, line_buffer):
        """Extract 'today tasks' from 'todo_today table' and 'add_today_task' area."""
        todo_today = []
        for line in line_buffer:
            if line == self.tbl['todo']['today']['tbl_header']:
                continue
            foo = re.search(self.tbl['re']['today']['tbl_task_line'], line)
            if foo:
                est = foo.group(1).strip()
                est = 0 if '' == est else int(est)
                sta = re.search(r"[Oo][Kk]", foo.group(2).strip())
                sta = 1 if sta else 0
                pom = foo.group(3).strip()
                pom = 0 if '' == pom else int(pom)
                task = foo.group(4).strip()
                todo_today.append({'est': est, 'sta': sta, 'pom': pom, 'task': task})
            else:
                foo = re.search(self.tbl['re']['today']['add_task_line'], line)
                if foo:
                    est = foo.group(1).strip()
                    est = int(est) if est != '' else 0
                    task = foo.group(2).strip()
                    todo_today.append({'est': est, 'task': task, 'sta': 0, 'pom': 0})
        return todo_today

    def _parse_todo_sometime(self, line_buffer):
        """Extract and classify 'add/remove sometime/tomorrow task' items"""
        todo_sometime = {'+': [], '-': [], '/': []}
        for line in line_buffer:
            sometime_tbl_line = re.search(self.tbl['re']['sometime']['add_task_line'], line)
            if sometime_tbl_line:
                task = sometime_tbl_line.group(2).strip()
                if task:
                    todo_sometime[sometime_tbl_line.group(1)].append(sometime_tbl_line.group(2).strip())
        return todo_sometime

# ---------------------------------------------------------------------------------------------------------------------

    def _todo_today_save(self, todo_info):
        """Save extracted todo today info to history db"""

        if (self.todo_db_history.contains(db.Query().date == todo_info['date'])):
            db_item_list = self.todo_db_history.get(db.Query().date == todo_info['date'])['todo_item']
            for today_item in todo_info['today']:
                for db_item in db_item_list:
                    if today_item['task'] == db_item['task']:
                        # update existing task
                        db_item['est'] = today_item['est']
                        db_item['sta'] = today_item['sta']
                        db_item['pom'] += today_item['pom']
                        break
                else:
                    if 0 != today_item['pom']:
                        db_item_list.append(today_item)  # add new task
            self.todo_db_history.update({'todo_item': db_item_list, 'time_evening': self._get_timestamp()['time']}, db.Query().date == todo_info['date'])
        else:
            todo_item_completed = [item for item in todo_info['today'] if item['pom'] != 0]
            bar = {'date': todo_info['date'], 'time_morning': todo_info['time'], 'time_evening': self._generate_timestamp()['time'], 'todo_item': todo_item_completed}
            self.todo_db_history.insert(bar)

        # clear just saved 'pom' counters
        for item in todo_info['today']:
            item['pom'] = 0

    def _todo_sometime_save(self, todo_info):
        """Save extarcted todo sometime info to history db"""

        for item in todo_info['sometime']['+']:
            if not self.todo_db_sometime.contains(db.Query().task == item):
                self.todo_db_sometime.insert({'task': item, 'date': todo_info['date']})

        for item in todo_info['sometime']['-']:
            self.todo_db_sometime.remove(db.Query().task == item)
            self.todo_db_tomorrow.remove(db.Query().task == item.replace(self.tbl['todo']['sometime_tomorrow_tag'], ''))

        for item in todo_info['sometime']['/']:
            if not self.todo_db_tomorrow.contains(db.Query().task == item):
                self.todo_db_tomorrow.insert({'task': item, 'date': todo_info['date']})

        # clear just processed todo sometime tasks
        todo_info['sometime'] = {'+': [], '-': [], '/': []}

    def _extract_todo_info(self, extract_history=False):
        """Read todo.pom and extract todo info (timestamp, shortterm tasks&est&pom&sta, sometime todo)"""
        line_buffer = self.util.file.load(self.todo_pom, 'txt', rstrip='\n')
        todo_info = {}
        todo_info['buffers'] = self._extract_todo_tbl_buffers(line_buffer, extract_history)
        todo_info['date'], todo_info['time'] = self._parse_timestamp_header(todo_info['buffers']['timestamp'])
        todo_info['today'] = self._parse_todo_today(todo_info['buffers']['today'])
        todo_info['sometime'] = self._parse_todo_sometime(todo_info['buffers']['sometime'])
        # self.info(todo_info['today'])
        return todo_info

    def _add_tasks2menu(self, tasks):
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

    def _update_todo_info(self):
        todo_info = self._extract_todo_info(True)
        self._add_tasks2menu(item['task'] for item in todo_info['today'])
        self._todo_sometime_save(todo_info)
        todo_today_tbl = self._generate_todo_today(tasks4tbl=todo_info['today'])
        todo_sometime_tbl = self._generate_todo_sometime() + [''] if todo_info['buffers']['sometime'] else []
        todo_history_tbl = self._generate_todo_history() if todo_info['buffers']['history'] else []
        self.util.file.save(todo_info['buffers']['timestamp'] + [''] + todo_today_tbl + [''] + todo_sometime_tbl + todo_history_tbl, self.todo_pom, 'txt', eol='\n')
        return

# API methods
    def todo_menu_cmd(self, cmd, task):
        self.info(cmd)
        self.info(task)
        return

    def todo_tbl_new(self, show_todo_sometime=False, show_todo_history=False):
        """
        Generate TODO tables and save them to todo.pom

        Args:
        show_todo_sometime -- turn on/off TODO sometime table printing
        show_todo_history -- turn on/off TODO history table printing

        Generate empty TODO today, history(optional) and sometime(optional) tables
        """

        pending_tasks = [item['task'] for item in self.todo_db_tomorrow.all()]
        self.todo_db_tomorrow.purge()
        todo_today_tbl = self._generate_todo_today(pending_tasks=pending_tasks)
        todo_sometime_tbl = self._generate_todo_sometime() + [''] if show_todo_sometime else []
        todo_history_tbl = self._generate_todo_history() if show_todo_history else []
        self.util.file.save([self._generate_timestamp_header()['day_time'], ''] + todo_today_tbl + [''] + todo_sometime_tbl + todo_history_tbl, self.todo_pom, 'txt', eol='\n')

    def todo_tbl_save(self):
        """Extract todo info from todo.pom and save it to db. Regenerate todo.pom with updated history"""
        todo_info = self._extract_todo_info(True)
        self._todo_today_save(todo_info)
        self._todo_sometime_save(todo_info)
        todo_today_tbl = self._generate_todo_today(tasks4tbl=todo_info['today'])
        todo_sometime_tbl = self._generate_todo_sometime() + [''] if todo_info['buffers']['sometime'] else []
        todo_history_tbl = self._generate_todo_history() if todo_info['buffers']['history'] else []
        self.util.file.save(todo_info['buffers']['timestamp'] + [''] + todo_today_tbl + [''] + todo_sometime_tbl + todo_history_tbl, self.todo_pom, 'txt', eol='\n')

    def todo_tbl_view(self, show_todo_sometime=False, show_todo_history=False):
        """
        Regenerate todo.pom with given settings

        Args:   show_todo_sometime - show todo sometime tbl to todo.pom
                show_todo_history - show todo history tbl to todo.pom
`
        TODO timestamp and TODO today are present by default, TODO sometime & history - optional
        """

        todo_info = self._extract_todo_info(True)
        todo_sometime_tbl = self._generate_todo_sometime() + [''] if show_todo_sometime else []
        todo_history_tbl = self._generate_todo_history() if show_todo_history else []
        self.util.file.save(todo_info['tbl_buffer']['timestamp'] + [''] + todo_info['tbl_buffer']['today'] + [''] + todo_sometime_tbl + todo_history_tbl, self.todo_pom, 'txt', eol='\n')

    def main(self, **kwargs):
        self.todo_tbl_new(True, True)
        # self.todo_tbl_view(True, True)
        # self.todo_tbl_save()
        # self.todo_db_holes.purge()
        # self.todo_db_holes.insert({'year': 2017, 'Holidays': ['2017/10/14'], 'Vacation': ['2017/10/10'], 'Sick': ['2017/10/03']})
        # self._extract_todo_info(True)
        # self._update_todo_info()
        return


if __name__ == "__main__":
    Todo_window().run()