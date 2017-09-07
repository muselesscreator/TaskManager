#!/usr/bin/python
import os
import argparse
from devlogger import devlog

HOME_DIR = '%s/Dev/TaskManager' % os.environ['HOME']
PREFS_PATH = '%s/prefs.txt' % HOME_DIR
NAME = 'name'
LIST = 'list'
TXT_EXT = '.txt'
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
        tasks = []
        task_types = {}
        targets = [SHORTTERM, LONGTERM, WAIT, BACKLOG]
        for target in targets:
            task_types[target] = []
        if os.path.isfile(fn):
            with open(fn) as fs:
                tasks =  filter(lambda l: l != '', fs.read().split('\n'))

        target_index = 0 
        for task in tasks:
            if task == TERM_DELIMITER:
                target_index += 1
                continue
            task_types[targets[target_index]].append(task)
        return task_types

                
    def _get_lists(self):
        return [l for l in os.listdir('%s/lists' % self._path) if l.endswith('.txt')]

    def _load_list(self):
        self._task_file = '%s/lists/%s' % (self._path, self._active_list)
        self._task_lists = self.read_from_file(self._task_file)

    def set_mode(self, mode):
        self._mode = mode

    def change_default(self, new):
        if not new.endswith(TXT_EXT):
            new += TXT_EXT
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
                ind = next(i for (i, v) in enumerate(words)
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

    @property
    def lists(self):
        return {SHORTTERM: {NAME: 'Short-Term', LIST: self.st_tasks},
                LONGTERM: {NAME: 'Long-Term', LIST: self.lt_tasks},
                BACKLOG: {NAME: 'Backlog', LIST: self.backlog_tasks},
                WAIT: {NAME: 'Wait/Watch', LIST: self.wait_tasks}};

    def display(self, st_only=True):
        print LINE_BREAK
        print 'List: %s' % self._active_list[:-4]
        print LINE_BREAK

        def display_list(task_list):
            print "%s Tasks" % task_list[NAME]
            print LINE_BREAK
            for i in range(len(task_list[LIST])):
                print self.word_wrap("%s:   %s" % (i, task_list[LIST][i]))
            print LINE_BREAK

        if not st_only:
            for mode in self.lists:
                display_list(self.lists[mode])
        else:
            display_list(self.lists[self._mode])

    def move_list(self, new_name):
        if "%s.txt" % new_name in self._lists:
            resp = raw_input("A file with that name exists." +
                         "Would you like to replace it? (y/N)")
            if resp != 'y':
                return
            os.rename(self._task_file, '%s/lists/%s.txt' % (self._path, new_name))
        else:
            os.rename(self._task_file, '%s/lists/%s.txt' % (self._path, new_name))
        self.change_default(new_name)

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
        print LINE_BREAK
        print self.word_wrap("%s:   %s" % (index, self.selected_list[index]))
        print LINE_BREAK
        resp = raw_input("= Delete Tasks (y/N): ")
        if resp.lower() == 'y':
            self._delete_task(index)
        print LINE_BREAK
        print '\n'

    def _delete_task(self, index):
        del self.selected_list[index]
        self._write_changes()

    def finish_task(self, index):
        print LINE_BREAK
        print self.word_wrap("%s:   %s" % (index, self.selected_list[index]))
        print LINE_BREAK
        resp = raw_input("= Finish Tasks (y/N): ")
        if resp.lower() == 'y':
            devlog("Finished task: %s" % self.selected_list[index])
            self._delete_task(index)
        print LINE_BREAK
        print '\n'

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
            self._change_type(index, targets[int(resp)-1])
        else:
            print "Cancelling"
        self._write_changes()

    def _change_type(self, index, new_list):
        task = self.selected_list[index]
        print LINE_BREAK
        print self.word_wrap("%s:   %s" % (index, task))
        print LINE_BREAK
        resp = raw_input("= Move task from %s list to %s list? (y/N): " % 
                         (self._mode, new_list))
        if resp.lower() == 'y':
            self._delete_task(index)
            self._task_lists[new_list].append(task)
            self._mode = new_list
        print LINE_BREAK
        print '\n'
