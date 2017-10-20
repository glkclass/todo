import re
# import datetime
from Scrpt import Scrpt
import tinydb as db
import operator

class Todo(Scrpt):
    """Support TODO-table usage"""
    param = {
                'path2do.pom':      'todo.pom',
                'path2do.db':       'todo.json',
                'path2do.cache':    'todo_cache.json',
                'cache_size':       8,
                'history':          {'re': '2017/10/\d\d', 'max_length': 0}
            }


    # re_patt =   {
    #                 'text': r'.+',
    #                 'number': r'\d+',
    #                 'add': r'[+-]',
    #                 'sep': r' *\| *'
    #             }

    tbl =   {
        'task_ph': 'taaask', 'pom_ph': 'pooom', 'add_ph': '+',
        'sep': ['|_', '_|_', '_|', '| ', ' | ', ' |'],
        'sep_': ['-', '-|-', '|']}


    tbl_component = {
            'todo_': {
                        'doubleline': 80 * '=',
                        'singleline': 80 * '-',
                        'todo_tbl_header': '|-EST-|-STA-|-POM-|-TASK-',
                        'todo_tbl_line': '|%s|%s|%s|%s',
                        'ph_line': '|' + 3 * ('     %s' % tbl['sep_'][2]) + ' ',

                        'todo_longterm_tbl_header': 'TODO:\n+\n-',                        
                    },

            'todo': {
                        # |_<#>_|_ ___________<Task>__________________z_|_<Est>_|_<Act>_|_<Sts>_|
                        'frmt_header': tbl['sep'][0] + '<#>' + tbl['sep'][1] + '%s' + tbl['sep'][1] + '<Est>' + tbl['sep'][1] + '<Act>' + tbl['sep'][1] + '<Sts>' + tbl['sep'][2],
                        'frmt_line': tbl['sep'][3] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][5]
                    },

            're': {
                    'doubleline': r'^ *=+ *$',
                    'singleline': r'^ *-+ *$',

                    # Today: 2017, Wk 40, Tue, Oct 03, 11:33:59
                    'timestamp_header': r'^ *Today: (\d{4}), Wk \d{2}, \w{3}, (\w{3}) (\d{2}), (\d{2}):(\d{2}):(\d{2}) *$',
                    # -Est-|-Sts-|-Pom-|-Task-
                    'todo_tbl_header': r'^ *-Est-\|-Sts-\|-Pom-\|-Task- *$',
                    #  5  |  Ok   |  5   | .*
                    'todo_tbl_line': r'^(.*)\|(.*)\|(.*)\|(.*)$',
                    # TODO:
                    'todo_longterm_tbl_header': r'^ *TODO: *$',
                    # + xxx
                    # - yyy
                    'todo_longterm_tbl_line': r'^ *(\+|-)(.*)$'



                    # 'task&est': r'^%s(%s)%s(%s)%s(%s)%s$' % (re_patt['sep'], re_patt['text'], re_patt['sep'], re_patt['number'], re_patt['sep'], re_patt['add'], re_patt['sep'])
                  }
        }





    def __init__(self, path2log=None, user_settings=None):
        """
        Todo constructor.

        Args:
        path2log, user_settings -- See 'Scrpt' class doc for details.

        Call superclass constructor, prepare parameters, open db.
        """
        Scrpt.__init__(self, path2log, user_settings)
        self.holidays =  {
                        'Holidays': ['2017/01/01', '2017/01/07']
                    }
        self.todo_db = db.TinyDB(self.param['path2do.db'], indent=2)


    def gen_timestamp(self):
        """Get current date/time stamp. Return dict with date/time values + date&time formatted strings."""
        foo = self.util.log.get_time()
        self.timestamp =    {   
                                # 'year': foo['now'].year, 'month': foo['now'].month, 'day': foo['now'].day,
                                # 'hour': foo['now'].hour, 'minute': foo['now'].minute,
                                'date': foo['date'],
                                'time': foo['time_wo_s'],
                            }
        return self.timestamp


    def get_timestamp_header(self, date=None, time=None):
        """Get formatted timestamp strings. Return dict with current week, day, ..."""
        if not date or not time:
            timestamp = self.gen_timestamp()
        else:
            timestamp = {'date': date, 'time': time}
        ymd = timestamp['date'].split('/')
        timestamp.update({'year': int(ymd[0]), 'month': int(ymd[1]), 'day': int(ymd[2])})

        week = self.log.get_week(timestamp['date'])
        month = self.log.month[timestamp['month']]
        foo = {}
        foo['week'] = '%04d, Wk %02d' % (timestamp['year'], week['num'])
        foo['day'] = '%s, %s %02d, %s' % (week['day'], month, timestamp['day'], timestamp['time'])
        foo['week&day'] = ', '.join((foo['week'], foo['day']))
        return foo

    def gen_todo_tbl(self, read4cache=False):
        """Generate TODO table part"""
        if not read4cache:  # generate empty TODO table
            self.save_todo_cache(self.extract_todo_tbl(self.util.file.load(self.param['path2do.pom'], 'txt')))  # push current todo tbl to the cache
            foo = []
            foo.append(self.tbl_component['todo_']['doubleline'])
            foo.append('Today: %s' % self.get_timestamp_header()['week&day'])
            foo.append(self.tbl_component['todo_']['singleline'])
            foo.append(self.tbl_component['todo_']['todo_tbl_header'])
            # # add pending tasks (incompleted from previous working session)
            # for item in pndg.keys():
            #     foo.append('\t' + self.tbl_component['tmpl']['pndg_frmt_line'] % (item, pndg[item]['est'])) 
            for i in range(7):  # new task placeholders
                foo.append(self.tbl_component['todo_']['ph_line'])
            foo.append(self.tbl_component['todo_']['singleline'])
            foo.append(self.tbl_component['todo_']['todo_longterm_tbl_header'])  # placeholders for longterm tasks
            foo.append(self.tbl_component['todo_']['doubleline'])
        else:  # read TODO table content from cache
            todo_cache = self.util.file.load(self.param['path2do.cache'], 'json')
            if todo_cache and type(todo_cache) is list and len(todo_cache) > 0:
                foo = todo_cache.pop(0)
                self.util.file.save(todo_cache, self.param['path2do.cache'], 'json')
            else:
                foo = ['The cache is empty or can\'t be read!']

        bar = self.get_todo_tbl_history()

        return foo + bar

    def save_todo_tbl(self):
        """Generate TODO table and save it to txt file (*.pom)"""
        self.util.file.save(self.gen_todo_tbl(False), self.param['path2do.pom'], 'txt')

    def save_todo_cache(self, foo):
        """Save current TODO table content to cache"""
        if len(foo) > 2:  # check the TODO table was really found & extracted
            if self.util.path.exists(self.param['path2do.cache']):
                todo_cache = self.util.file.load(self.param['path2do.cache'], 'json')
                if len(todo_cache) >= self.param['cache_size'] :
                    todo_cache.pop(-1)
                todo_cache.insert(0, foo)
                self.util.file.save(todo_cache, self.param['path2do.cache'], 'json')
            else:
                self.util.file.save([foo], self.param['path2do.cache'], 'json')

    def extract_todo_tbl(self, todo_tbl_buffer):
        """Extract TODO table content bounded by start/stop markers from txt buffer"""
        todo_tbl = []  # TODO table
        todo_tbl_started = False
        for line in todo_tbl_buffer:
            if line:
                startstop_marker = re.search(self.tbl_component['re']['doubleline'], line)
                if startstop_marker:
                    todo_tbl.append(line)
                    if not todo_tbl_started:
                        todo_tbl_started = True
                    else:
                        break
                else:
                    if todo_tbl_started is True:
                        todo_tbl.append(line)
        else:
            self.log.error('TODO table corrupted: no stop marker')
        return todo_tbl

    def extract_todo_info(self, todo_tbl):
        """Extract TODO info (timestamp, shortterm tasks&est&pom&sts, longterm TODO) from TODO table"""
        todo_info = {}
        # for line in todo_tbl:
        #     self.log.info(line)
        timestamp_header_found = False
        todo_tbl_header_found = False
        todo_tbl_finished = False
        todo_longterm_tbl_header_found = False
        for line in todo_tbl:
            if not timestamp_header_found:
                timestamp_header = re.search(self.tbl_component['re']['timestamp_header'], line)  # find timestamp header
                if timestamp_header:
                    timestamp_header_found = True
                    # Today: 2017, Wk 40, Tue, Oct 03, 11:33:59
                    todo_date = '%04s/%02s/%02s' % (timestamp_header.group(1), self.log.month.index(timestamp_header.group(2)), timestamp_header.group(3))
                    todo_info['time'] = '%02s:%02s:%02s' % (timestamp_header.group(4), timestamp_header.group(5), timestamp_header.group(6))
            elif not todo_tbl_header_found:
                todo_tbl_header = re.search(self.tbl_component['re']['todo_tbl_header'], line)  # find TODO tbl header
                todo_tbl_header_found = True if todo_tbl_header else False
                if todo_tbl_header:
                    todo_tbl_header_found = True
                    todo_info['todo'] = {'item': []}
                    # self.log.info(todo_tbl_header.group(0))
            elif not todo_tbl_finished:
                todo_tbl_line = re.search(self.tbl_component['re']['todo_tbl_line'], line)
                if todo_tbl_line:
                    todo_info['todo']['item'].append({'est': todo_tbl_line.group(1).strip(), 'sts': todo_tbl_line.group(2).strip(), 'pom': todo_tbl_line.group(3).strip(), 'task': todo_tbl_line.group(4).strip()})
                else:
                    todo_tbl_finish_marker = re.search(self.tbl_component['re']['singleline'], line)
                    todo_tbl_finished = True if todo_tbl_finish_marker else False
                    # if todo_tbl_finish_marker:
                    #     self.log.info(todo_tbl_finish_marker.group(0))
            elif not todo_longterm_tbl_header_found:
                todo_longterm_tbl_header = re.search(self.tbl_component['re']['todo_longterm_tbl_header'], line)  # find TODO tbl header
                todo_longterm_tbl_header_found = True if todo_longterm_tbl_header else False
                todo_info['todo_longterm'] = {'+': [], '-': []}
                # if todo_longterm_tbl_header:
                #     self.log.info(todo_longterm_tbl_header.group(0))
            else:
                # self.tbl_component['re']['todo_longterm_tbl_line'] = r'^ *(\+|-) *(.*) *$'
                todo_longterm_tbl_line = re.search(self.tbl_component['re']['todo_longterm_tbl_line'], line)
                if todo_longterm_tbl_line:
                    todo_info['todo_longterm'][todo_longterm_tbl_line.group(1)].append(todo_longterm_tbl_line.group(2).strip())
                else:
                    finish_marker = re.search(self.tbl_component['re']['doubleline'], line)
                    if finish_marker:
                        # self.log.info(finish_marker.group(0))
                        break  # 'TODO part found' conformation
        else:
            self.log.error('TODO table corrupted!!!')
        return todo_date, todo_info

    def parse_todo_info_content(self, todo_info):
        """Parse TODO table items"""
        for item in todo_info['todo']['item']:
            # self.log.info('-%s-%s-%s-%s' % (item['est'], item['sts'], item['pom'], item['task']))
            est = re.search(r"^[^\d]*(\d+).*$", item['est'])
            item['est'] = int(est.group(1)) if est else 0

            sts = re.search(r"^[Oo]*[Kk]*.*$", item['sts'])
            item['sts'] = 1 if sts else 0

            pom_arr = item['pom'].split('+')
            pom = 0
            for i in range(len(pom_arr)):
                foo = re.search(r'^ *(\d+) *$', pom_arr[i])
                if foo:
                    pom += int(foo.group(1))
            item['pom'] = pom
            # self.log.info('-%s-%s-%s-%s' % (item['est'], item['sts'], item['pom'], item['task']))
        return todo_info

    def get_todo_info(self):
        """Read todo.pom and extract todo info (timestamp, shortterm tasks&est&pom&sts, longterm todo)"""
        todo_tbl_buffer = self.util.file.load(self.param['path2do.pom'], 'txt')
        todo_tbl = self.extract_todo_tbl(todo_tbl_buffer)
        todo_date, todo_info = self.extract_todo_info(todo_tbl)
        todo_info = self.parse_todo_info_content(todo_info)

        if not todo_tbl or not todo_date or not todo_info:
            self.log.error('TODO table info wasn\'t found!')
            return {'todo_date': None, 'todo_tbl': None, 'todo_info': None}
        else:
            # self.log.info(todo_info)
            # self.log.info(todo_tbl)
            return {'todo_date': todo_date, 'todo_tbl': todo_tbl, 'todo_info': todo_info}


    def db_update(self):
        """Extract todo info and save it to todo.db."""
        foo = self.get_todo_info()
        todo_item_completed = [item for item in foo['todo_info']['todo']['item'] if item['pom'] != 0]        
        if (self.todo_db.contains(db.Query().date == foo['todo_date'])):
            self.todo_db.update({'todo_item': todo_item_completed}, db.Query().date == foo['todo_date'])
        else:
            bar = {'date': foo['todo_date'], 'time': foo['todo_info']['time'], 'todo_item': todo_item_completed}
            self.todo_db.insert(bar)


    def get_todo_tbl_history(self):
        """Generate history part of TODO table. History duration, stop date etc are defined by settings."""

        history = self.todo_db.search((db.Query().date.search(self.param['history']['re'])))
        history.sort(key=operator.itemgetter('date'))
        history.reverse()
        # self.log.info(history)
        history_buffer = []
        for day in history:
            week = self.log.get_week(day['date'])
            headers = self.get_timestamp_header(day['date'], day['time'])

            if 'Fri' == week['day']:
                history_buffer.append(headers['week'] + '\n')
            history_buffer.append('  ' + headers['day'])
            history_buffer.append('    ' + self.tbl_component['todo_']['todo_tbl_header'])
            
            for item in day['todo_item']:
                todo_tbl_line = (self.util.allign_text(str(item['est']), 5), 
                                 self.util.allign_text({0: '', 1: 'Ok'}[item['sts']], 5), 
                                 self.util.allign_text(str(item['pom']), 5), 
                                 self.util.allign_text(str(item['task']), 5), 
                                 )
                history_buffer.append('    ' + self.tbl_component['todo_']['todo_tbl_line'] % todo_tbl_line)
            history_buffer.append('')

        # self.log.info (history_buffer)
        


        return history_buffer






    def test_db(self):
        
        # self.log.info(db.all())
        # history = tinydb.Query()
        # for item in iter (self.todo_db):
        #     self.log.info(item)
        self.log.info(self.todo_db.all())
        



        
    def main(self, **kwargs):
        self.save_todo_tbl()
        # foo = self.get_todo_info()
        # self.get_timestamp_header()
        # self.test_db()
        # self.db_update()
        # self.gen_todo_tbl()

        return
        

# todo.save_todo_tbl_tmpl()
# todo.add_todo_tasklist()
# todo.gen_todo_dot_pom(todo.open_db())




settings = {'print_cmd': False}
Todo(user_settings=settings).run()
