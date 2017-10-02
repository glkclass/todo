import re
import datetime
from Scrpt import Scrpt


class Todo(Scrpt):
    param = {
                'path2do.pom':      'todo.pom',
                'path2do.db':       'todo.json',
                'path2do.cache':    'todo_cache.json',
                'cache_size':       8,
                'todo_tbl_error': 'Task&Estimation data wasn\'t found!',
            }


    re_patt =   {
                    'text': r'.+',
                    'number': r'\d]+',
                    'add': r'[+-]',
                    'sep': r' *\| *'
                }

    tbl =   {
        'task_ph': 'taaask', 'pom_ph': 'pooom', 'add_ph': '+',
        'sep': ['|_', '_|_', '_|', '| ', ' | ', ' |'],
        'sep_': ['-', '-|-', '|']}


    tbl_component = {
            'todo_':{
                    'doubleline': 80 * '=',
                    'singleline': 80 * '-',
                    'header': '%sEst%sSts%sPom%sTask%s' % (tbl['sep_'][0], tbl['sep_'][1], tbl['sep_'][1], tbl['sep_'][1], tbl['sep_'][0]),                    
                    'ph_line': 3 * ('     %s' % tbl['sep_'][2]) + ' ',
                    'todo_longterm': 'TODO:\n+\n-',
                    'pndg_frmt_line': tbl['sep'][3] + 2 * ('%s' + tbl['sep'][4]) + '+' + tbl['sep'][5]
                },

            'todo':     {
                    # |_<#>_|_ ___________<Task>__________________z_|_<Est>_|_<Act>_|_<Sts>_|
                    'frmt_header': tbl['sep'][0] + '<#>' + tbl['sep'][1] + '%s' + tbl['sep'][1] + '<Est>' + tbl['sep'][1] + '<Act>' + tbl['sep'][1] + '<Sts>' + tbl['sep'][2],
                    'frmt_line': tbl['sep'][3] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][4] + '%s' + tbl['sep'][5]

                },

            're':   {
                    'task&est': r'^%s(%s)%s(%s)%s(%s)%s$' % (re_patt['sep'], re_patt['text'], re_patt['sep'], re_patt['number'], re_patt['sep'], re_patt['add'], re_patt['sep'])
                }
        }





    def __init__(self, path2log=None, user_settings=None):
        self.holidays =  {
                        'Holidays': ['2017/01/01', '2017/01/07']
                    }
        Scrpt.__init__(self, path2log, user_settings)

    def get_time_stamp(self):
        """Get current date/time stamp"""
        foo = self.util.log.get_time()
        timestamp =    {   'db':   {
                                        'year': foo['now'].year, 'month': foo['now'].month, 'day': foo['now'].day,
                                        'hour': foo['now'].hour, 'minute': foo['now'].minute, 'second': foo['now'].second
                                    },
                            'date': foo['date']
                        }
        return timestamp

    def get_week(self, time_stamp):
        return  {
                    'num': datetime.date(time_stamp['db']['year'], time_stamp['db']['month'], time_stamp['db']['day']).isocalendar()[1],
                    'day': self.log.weekday[datetime.date(time_stamp['db']['year'], time_stamp['db']['month'], time_stamp['db']['day']).weekday()]
                }

    def get_timestamp_header(self, timestamp=None):
        if not timestamp:
            timestamp = self.get_time_stamp()
        week = self.get_week(timestamp)
        month = self.log.month[timestamp['db']['month']]
        todo_time = '%02d:%02d:%02d' % (timestamp['db']['hour'], timestamp['db']['minute'], timestamp['db']['second'])
        foo = {}
        foo['week'] = '%04d, Wk %02d' % (timestamp['db']['year'], week['num'])
        foo['day'] = '%s, %s %02d, %s' % (week['day'], month, timestamp['db']['day'], todo_time)
        foo['week&day'] = ', '.join((foo['week'], foo['day']))
        return foo

    def gen_todo_tbl(self, read4cache=False, pndg={}):
        """Generate TODO table part"""
        if not read4cache:  # generate empty TODO table
            self.save_todo_cache(self.extract_todo_info())
            foo = []
            foo.append(self.tbl_component['todo_']['doubleline'])
            foo.append ('Today: %s' % self.get_timestamp_header()['week&day'])
            foo.append(self.tbl_component['todo_']['singleline'])
            foo.append(self.tbl_component['todo_']['header'])
            # # add pending tasks (incompleted from previous working session)
            # for item in pndg.keys():
            #     foo.append('\t' + self.tbl_component['tmpl']['pndg_frmt_line'] % (item, pndg[item]['est'])) 
            for i in range(7):  # new task placeholders
                foo.append(self.tbl_component['todo_']['ph_line'])
            foo.append(self.tbl_component['todo_']['singleline'])
            foo.append(self.tbl_component['todo_']['todo_longterm'])  # placeholders for longterm tasks
            foo.append(self.tbl_component['todo_']['doubleline'])
        else:  # read TODO table content from cache
            todo_cache = self.util.file.load(self.param['path2do.cache'], 'json')
            if todo_cache and type(todo_cache) is list and len(todo_cache) > 0:
                foo = todo_cache.pop(0)
                self.util.file.save(todo_cache, self.param['path2do.cache'], 'json')
            else:
                foo = ['The cache is empty or can\'t be read!']
        return foo

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

    def extract_todo_info(self):
        """Read todo.pom file and extract TODO info (timestamp, shortterm tasks&est&pom&sts, longterm TODO)"""
        foo = self.util.file.load(self.param['path2do.pom'], 'txt')

        # Read *.pom file and extract TODO table
        todo_tbl = []  # Task&Estimation table
        todo_tbl_started = False
        todo_tbl_finished = False
        for i in range(len(foo)):
            if foo[i].strip():
                if self.tbl_component['todo_']['doubleline'] == foo[i]:
                    todo_tbl.append(foo[i])
                    if not todo_tbl_started:
                        todo_tbl_started = True
                    else:
                        todo_tbl_finished = True
                else:
                    if todo_tbl_finished is True:
                        break
                    else:
                        if todo_tbl_started is True:
                            todo_tbl.append(foo[i])
        return todo_tbl

        XXX
        
        # Extract TODO info
        todo_tl = []
        if todo_tbl_started is True and todo_tbl_finished is True:
            for line in todo_tbl:
                bar = re.search(self.tbl_component['re']['task&est'], line)  # check Task&Etsimation line is correct
                if bar:
                    if self.tbl['task_ph'].strip() != bar.group(1).strip():
                        todo_tl.append({'name': bar.group(1).strip(), 'est': bar.group(2), 'add': bar.group(3)})

        if not todo_tl:
            self.log.fatal(self.param['todo_tbl_error'])
        else:
            pass
            # self.log.info(todo_tl)

        return todo_tl


    def open_db(self):
        """Open TODO database (history)"""
        db = self.util.file.load(self.param['path2do.db'], 'json')
        db = {} if db is None else db
        return db

    def add_new_todo_tasklist(self, db, todo_tl, time_stamp):
        """Add new TODO.db record"""
        db_rec = {'time_stamp': time_stamp['db']}
        db_rec['tasklist'] = []
        for item in todo_tl:
            if '+' == item['add']:
                db_rec['tasklist'].append({'name': item['name'], 'act': 0, 'sts': 'todo', 'est': item['est']})
        db[time_stamp['date']] = db_rec
        return db

    def update_existing_todo_tasklist(self, db, todo_tl, time_stamp):
        """Update existing TODO.db record"""
        db_rec = db[time_stamp['date']]

        db_rec_tasklist = [db_rec['tasklist'][idx]['name'] for idx in range(len(db_rec['tasklist']))]

        for item in todo_tl:
            if item['name'] not in db_rec_tasklist:  #  new task
                if '+' == item['add']:
                    db_rec['tasklist'].append({'name': item['name'], 'act': 0, 'sts': 'todo', 'est': item['est']})  # add task to todo list if 'add' = '+'
            else:  # task already in the list
                task_idx = self.get_tasklist_idx(todo_tl, item['name'])
                if '+' == item['add']:
                    db_rec['tasklist'][task_idx]['est'] = item['est']  # update estimation for existing task if 'add' = '+'
                elif '-' == item['add']:
                    db_rec['tasklist'].pop(task_idx)  # remove existing task from todo list if 'add' = '-'

        db[time_stamp['date']] = db_rec
        return db

    def get_tasklist_idx (self, todo_tl, task_name):
        """Return task index inside tasklist if it is else return None"""
        for idx in range(len(todo_tl)):
            if task_name == todo_tl[idx]['name']:
                return idx
        else:
            return None  # no such task

    def add_todo_tasklist(self):
        """Extract TODO tasklist and: add it as new record to TODO.db or update existing one depending whether it already exists or no"""
        db = self.open_db()
        todo_tl = self.get_todo_tasklist()
        time_stamp = self.get_time_stamp()
        if time_stamp['date'] not in db.keys():
            db = self.add_new_todo_tasklist(db, todo_tl, time_stamp)
        else:
            db = self.update_existing_todo_tasklist(db, todo_tl, time_stamp)

        self.util.file.save('json', db, self.param['path2do.db'])
        self.gen_todo_dot_pom(db, time_stamp)

    def gen_todo_dot_pom(self, db):
        """Generate TODO table based on current date and DB content: template + today + history"""
        todo_dot_pom = self.gen_todo_tbl()  # generate TODO table template
        todo_dot_pom.append('')  # new line
        todo_dot_pom += self.gen_todo_tbl_history(db)  # generate todo history table
        self.util.file.save('txt', todo_dot_pom, self.param['path2do.pom'])  # save to file
        return todo_dot_pom


    def gen_todo_tbl_history(self, db):
    #     """Generate history part of TODO table. History duration, stop date etc are defined by settings."""
        days = db.keys()
        days.sort()
        last_week = abs(self.cfg['history']['last_week']) if 0 != self.cfg['history']['last_week'] else self.get_week(db[days[-1]]['time_stamp'])['num']
        first_week = last_week - abs(self.cfg['history']['num_weeks'])
        first_week = 1 if first_week < 1 else first_week
        first_day_idx = -len(days)
        pre_week_num = 0
        history = []
        day_idx = -1
        while day_idx >= first_day_idx:
            day_i = db[days[day_idx]]
            week_num = self.get_week(day_i['time_stamp'])['num']
            if week_num in range(first_week, last_week + 1):
                if pre_week_num != week_num:
                    pre_week_num = week_num
                    history.append(self.gen_week_header(day_i['time_stamp']))
                    history.append('')
                history.append(self.gen_day_header(day_i['time_stamp']))

                max_task_len = len('<Task>')
                for item in day_i['tasklist']:
                    max_task_len = len(item['name']) if len(item['name']) > max_task_len else max_task_len

                # todo table header
                history.append('\t' + self.tbl_component['todo']['frmt_header'] % self.util.allign_text('<Task>', max_task_len, 'center', '_'))


                for idx in range(len(day_i['tasklist'])):
                    task = day_i['tasklist'][idx]['name']
                    foo = (self.util.allign_text(str(idx), 3), self.util.allign_text(task, max_task_len), self.util.allign_text(str(day_i['tasklist'][idx]['est']), 5),
                           self.util.allign_text(str(day_i['tasklist'][idx]['act']), 5), self.util.allign_text(day_i['tasklist'][idx]['sts'], 5))
                    # todo table task/estimation/actual/status
                    history.append('\t' + self.tbl_component['todo']['frmt_line'] % foo)
                history.append('')
            elif week_num < first_week:
                break
            day_idx -= 1

        # self.log.info(history)
        return history
        pass




    def main(self, **kwargs):
        self.save_todo_tbl()
        


# todo.save_todo_tbl_tmpl()
# todo.add_todo_tasklist()
# todo.gen_todo_dot_pom(todo.open_db())




settings = {'print_cmd': False, 'history': {'year': 2017, 'num_weeks': 4, 'last_week': 0}}
Todo(user_settings=settings).run()
