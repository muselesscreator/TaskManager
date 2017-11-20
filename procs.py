import os
import re
import signal
from subprocess import Popen, PIPE, STDOUT
import time


class BWProcess(object):
    """
    Creates a wrapper around the subproces.Popen

    @param command             - The command to be run
    @param options{}           - Dictionary of options affecting how the command
                                    is to be run
           options.get_output  - returns stdout from run() method
           options.quiet       - doesn't print the stdout from run() method
    """
    def __init__(self, command, options=dict()):

        self.command = command

        def check_opt(key):
            return options and key in options and options[key]

        self._get_output = check_opt('get_output')
        self._quiet = check_opt('quiet')

        self.process = Popen(command, shell=True, stdout=PIPE,
                             stdin=PIPE, stderr=STDOUT)

    def write(self, stdin):
        # write <stdin> to the stdin stream of the process
        self.process.stdin.write(stdin)

    def passive_run(self):
        # return stdout and stderr or process without calling .communicate()
        stdout = self.process.stdout.readlines()
        stderr = self.process.stderr.readlines()
        return '\n'.join([stdout, stderr])

    def run(self):
        # run process and relinquish control of this thread to it until done.
        stdout, stderr = self.process.communicate()
        self.returncode = self.process.returncode

        self.stdout = stdout
        self.stderr = stderr

        if not self._quiet:
            print stdout
        if self._get_output:
            return stdout


def mk_process(command, options={'get_output': True, 'quiet': True}):
    """
    Simple wrapper around BWProcess class, which simplifies calls for the
       the most common use-case

    @arg command    - The command-line command to be run
    @arg options    - Pass-through to BWProcess options param

    @return         - The output of the run() method for the BWProcess
    """
    return BWProcess(command, options).run()


def getUserFromUID(uid):
    """
    Returns the username associated with the uid provided by a ps call.

    @arg uid         - The uid provided by a 'ps' call (int or str)

    @return          -(str) username associated with uid
    """
    if uid.isdigit():
        return mk_process('getent passwd "%s"' % uid).split(':')[0]
    else:
        return uid


def getOtherProcs(search_terms):
    """returns a list of process dictionaries for each non-self process matching
    the given search terms

    @param search_terms - regexp (or list of regexp) that must match the command
                          as reported in the ps %a field.

    @return             - [{uid, pid, name, command}] array of process dicts
    """
    if isinstance(search_terms, str):
        search_terms = [search_terms]

    def mk_proc(ps_line):
        """return an info dict from the ps line"""
        fields = ps_line.split()
        print fields
        return {
            "uid": fields[0],
            'pid':  int(fields[1]),
            'name': fields[2],
            'command': ' '.join(fields[3:]),
        }

    def matches(proc):
        """determine if the proc item matches search_terms"""
        return (proc['pid'] != os.getpid() and
                all(re.search(term, proc['command']) for term in search_terms))

    ps_output = mk_process('ps ahxw -o "%u %p %c %a"').strip().split('\n')
    procs = [mk_proc(s) for s in ps_output]
    return [p for p in procs if matches(p)]


def attemptToKillOtherProcs(search_terms, timeout=5):
    """
    Attempts to kill all non-self processes that match the given search terms
    Give up if the processes can't be killed after trying for a given length of time.

    @param search_terms - regexp (or list of regexp) that must match the command
                          as reported in the ps %a field.
    @param timeout      - (int) number of seconds to wait before giving up

    @return            - (bool) did I successfully kill all requested processes?
    """
    for proc in getOtherProcs(search_terms):
        try:
            os.kill(proc['pid'], signal.SIGTERM)
        except:
            pass

    start = time.time()
    while time.time() - start < timeout:
        if len(getOtherProcs(search_terms)) > 0:
            time.sleep(1)
        else:
            break

    return len(getOtherProcs(search_terms)) == 0
