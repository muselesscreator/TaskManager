#!/usr/bin/python
import os
import argparse
from devlogger import devlog

HOME_DIR = '%s/Dev/TaskManager' % os.environ['HOME']
PREFS_PATH = '%s/prefs.txt' % HOME_DIR
LINE_LENGTH = 64
LINE_BREAK = '=' * LINE_LENGTH
TERM_DELIMITER = '=' * 10
FIRST = 'first'
LAST = 'last'
UP = -1
DOWN = 1
WAIT = 'wait'
BACKLOG = 'backlog'
SHORTTERM = 'short-term'
LONGTERM = 'long-term'


class TaskManager(object):
    def __init__(self):
        self.line_length = 64 
        self._path = HOME_DIR

        if os.path.isfile(PREFS_PATH):
            with open(PREFS_PATH) as fs:
                self._prefs = fs.readlines()
        else:
            self._prefs = None

        self._mode = SHORTTERM

        self._active_list = ''
        self._task_file = ''
        self._task_lists = {
                SHORTTERM: [],
                LONGTERM: [],
                WAIT: [],
                BACKLOG: []}
        self._lists = self._get_lists()

        self._initialize_active_list()

    @property
    def st_tasks(self):
        return self._task_lists[SHORTTERM]

    @property
    def lt_tasks(self):
        return self._task_lists[LONGTERM]

    @property
    def wait_tasks(self):
        return self._task_lists[WAIT]

    @property
    def backlog_tasks(self):
        return self._task_lists[BACKLOG]

    @property
    def selected_list(self):
        return self._task_lists[self._mode]

    def _initialize_active_list(self):
        if self._prefs is not None:
            self._active_list = self._prefs[0]
            self._load_list()
        else:
            active_list = self._lists[0] if len(self._lists) else 'new_list'
            self.change_default(active_list)

    def _write_to_file(self, fn, text):
        f = open(fn, 'w')
        f.write(text)

    def read_from_file(self, fn):
        if not os.path.isfile(fn):
            print "Warning: read of %s failed" % fn
            return ['']
        else:
            with open(fn) as fs:
                return fs.read().split('\n')
                
    def _get_lists(self):
        return [l for l in os.listdir('%s/lists' % self._path) if l.endswith('.txt')]

    def _load_list(self):
        self._task_file = '%s/lists/%s' % (self._path, self._active_list)
        if os.path.isfile(self._task_file):
            tasks = filter(lambda l: l != '', self.read_from_file(self._task_file))
        else:
            tasks = []

        targets = [SHORTTERM, LONGTERM, WAIT, BACKLOG]
        for target in targets:
            self._task_lists[target] = []

        target_index = 0 
        for task in tasks:
            if task == TERM_DELIMITER:
                target_index += 1
                continue
            self._task_lists[targets[target_index]].append(task)

    def set_mode(self, mode):
        self._mode = mode

    def change_default(self, new):
        self._active_list = new
        self._write_to_file(PREFS_PATH, self._active_list)
        self._load_list()

    def word_wrap(self, text):
        border = 2
        text = text.rstrip()
        max_len = self.line_length - (border * 2)
        if len(text) > max_len:
            words = text.split(' ')
            try:
                ind = next(i for (i,v) in enumerate(words)
                        if len(' '.join(words[:i+1])) > max_len)
            except Exception, e:
                raise(e)

            line = ' '.join(words[:ind])

            line1 = '= %s%s =' % (' '.join(words[:ind]), ' '*(max_len-len(line)))
            line2 = self.word_wrap(' '*(2*border+1) + ' '.join(words[ind:]))
            return '%s\n%s' % (line1, line2)
        else:
            return '= ' + text + ' '*(max_len-len(text)) + ' ='
     
    def _write_changes(self):
        self._write_to_file(self._task_file,
                '\n'.join(self.st_tasks + [TERM_DELIMITER] +
                          self.lt_tasks + [TERM_DELIMITER] +
                          self.wait_tasks + [TERM_DELIMITER] +
                          self.backlog_tasks))

    def display(self):
        print LINE_BREAK
        print 'List: %s' % self._active_list[:-4]
        print LINE_BREAK

        for l in [{'name': 'Short-Term', 'list': self.st_tasks},
                  {'name': 'Wait/Watch', 'list': self.wait_tasks},
                  {'name': 'Long-Term', 'list': self.lt_tasks},
                  {'name': 'Backlog', 'list': self.backlog_tasks}]:
            print "%s Tasks" % l['name']
            print LINE_BREAK
            for i in range(len(l['list'])):
                print self.word_wrap("%s:   %s" % (i, l['list'][i]))
            print LINE_BREAK

    def move_list(self, new_name):
        if "%s.txt" % new_name in self._lists:
            resp = raw_input("A file with that name exists." +
                         "Would you like to replace it? (y/N)")
            if resp != 'y':
                return
            os.rename(self._task_file, '%s/lists/%s.txt' % (self._path, args.mv))
        else:
            os.rename(self._task_file, '%s/lists/%s.txt' % (self._path, args.mv))
        self.change_default(args.mv)

    def remove_list(self, name):
        resp = raw_input("Are you sure you want to delete the %s list? (y/N)" % name)
        if resp == 'y':
            os.remove('%s/lists/%s.txt' % (self._path, name))

    def show_lists(self):
        print "="*30
        print "= Available Lists:"
        print "="*30
        for l in self._lists:
            print ' = * %s' % l[:-4]
        print "="*30

    def prepend_task(self):
        print "Please type in a task to be prepended to the current list"
        self.selected_list.insert(0, raw_input())
        self._write_changes()

    def append_task(self):
        print "Please type in a task to be appended to the current list"
        self.selected_list.append(raw_input())
        self._write_changes()

    def delete_task(self, index):
        del self.selected_list[index]
        self._write_changes()

    def finish_task(self, index):
        devlog("Finished task: %s" % self.selected_list[args.f])
        self.delete_task(index)

    def move_task(self, index, new_slot=None, direction=None):
        if direction is not None:
            self.selected_list.insert(index+direction, self.selected_list.pop(index))
        elif new_slot is not None:
            if new_slot == FIRST:
                self.selected_list.insert(0, self.selected_list.pop(index))
            else:
                self.selected_list.append(self.selected_list.pop(index))
        self._write_changes()

    def change_type(self, index):
        task = self.selected_list[index]
        print "Change Task Type:"
        print task
        targets = [SHORTTERM, WAIT, LONGTERM, BACKLOG]
        for i, target in enumerate(targets):
            print "  %s: %s" % (i+1, target)
        resp = raw_input("Enter new type (1-4) or leave blank to cancel:  ")
        if int(resp) in [1, 2, 3, 4]:
            self.delete_task(index)
            self._task_lists[targets[int(resp)-1]].append(task)
        else:
            print "Cancelling"
        self._write_changes()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-lt", "--longterm", help="Modify long-term tasks", dest='lt', action="store_true")
    parser.add_argument("-w", "--wait", help="Modify Wait/Watcher tasks list", dest='w', action='store_true')
    parser.add_argument('-bl', '--backlog', help="Modify Backlog tasks list", dest='bl', action='store_true')
    parser.add_argument("-a", "--append", help="add a task to the end of the list", dest='a', action='store_true')
    parser.add_argument("-p", "--prepend", help="add a task to the beginning of the list", dest='p', action='store_true')
    parser.add_argument("-d", "--delete", help="delete the task at the given index", dest='d', type=int)
    parser.add_argument("-ct", "--changetype", help="change task at given index to new task type", dest='ct', type=int)
    parser.add_argument("-mu", "--moveup", help="move the selected task up in priority", dest='mu', type=int)
    parser.add_argument("-md", "--movedown", help="move the selected task down in priority", dest='md', type=int)
    parser.add_argument("-m1", "--promote", help="promote the selected task to top priority", dest='m1', type=int)
    parser.add_argument("-ml", "--demote", help="demote the selected task to bottom priority", dest='ml', type=int)
    parser.add_argument("-cd", "--change-list", help="Change lists", dest = 'cd')
    parser.add_argument("-rm", "--delete-list", help="Delete a list", dest = 'rm')
    parser.add_argument("-ls", "--list-lists", help="lists the ... lists", dest = 'ls', action="store_true")
    parser.add_argument("-mv", "--rename-list", help="rename the list", dest = 'mv')
    parser.add_argument("-f", "--finish", help="finish/log the task", dest='f', type=int)
    args = parser.parse_args()

    tsk_mgr = TaskManager()


    if args.lt:
        tsk_mgr.set_mode(LONGTERM)
    elif args.w:
        tsk_mgr.set_mode(WAIT)
    elif args.bl:
        tsk_mgr.set_mode(BACKLOG)

    if args.ls:
        tsk_mgr.show_lists()
    elif args.rm != None:
        tsk_mgr.remove_list(args.m)
    elif args.cd != None:
        tsk_mgr.change_default(args.cd)
        tsk_mgr.display()
    elif args.d != None:
        tsk_mgr.delete_task(args.d)
        tsk_mgr.display()
    elif args.f != None:
        tsk_mgr.finish_task(args.f)
        tsk_mgr.display()
    elif args.ct != None:
        tsk_mgr.change_type(args.ct)
        tsk_mgr.display()
    elif args.mu != None:
        tsk_mgr.move_task(args.mu, direction=UP)
        tsk_mgr.display()
    elif args.md != None:
        tsk_mgr.move_task(args.md, direction=DOWN)
        tsk_mgr.display()
    elif args.m1 != None:
        tsk_mgr.move_task(args.m1, new_slot=FIRST)
        tsk_mgr.display()
    elif args.ml != None:
        tsk_mgr.move_task(args.ml, new_slot=LAST)
        tsk_mgr.display()
    elif args.a:
        tsk_mgr.append_task()
        tsk_mgr.display()
    elif args.p:
        tsk_mgr.prepend_task()
        tsk_mgr.display()
    elif args.mv != None:
        tsk_mgr.move_list(args.mv)
        tsk_mgr.display()
    else:
        tsk_mgr.display()
