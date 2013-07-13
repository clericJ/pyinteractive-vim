# -*- coding: utf-8 -*-
"""
This module is part of vim PyInteractive plugin
"""
import sys
import vim
import optparse

from pyinteractiveilib import pythonshell
from pyinteractiveilib.completer import Completer

#logging.basicConfig(filename=LOG_FILENAME, filemode='w',level=logging.DEBUG)


_interpreter = pythonshell.VimInterpreter()

# Public Interface

def run():
    """ Run python read-eval-print loop, press <esc> to exit
    """
    _interpreter.interact()


def evaluate_line(line):
    """ Evaluate python code line in interpreter
        line - python code (str)
    """
    _interpreter.evaluate(line)


def evaluate_range():
    """ Evaluate current range in buffer
    """
    _interpreter.evaulate_range()


def execute_buffer():
    """ Run cuurent buffer in interpreter
    """
    _interpreter.execute_buffer()


def _restart():
    """ Restart interpreter
    """
    global _interpreter
    _interpreter = pythonshell.VimInterpreter()


def show_history(args=''):
    """ Display input/output history in current session
        args:
            -r          history in raw format
            -i          input only
            -o          output only
            -f <FILE>   write history to file
    """
    def parse_cmdline(args):
        """ parse_cmdline(args: str) -> list
        """
        result = []
        delimiter = False
        last_index = 0
        for index, char in enumerate(args):
            if char == " " and not delimiter:
                arg = args[last_index:index].lstrip().rstrip()
                if arg:
                    result.append(arg)
                    last_index = index

            elif char == '"':
                delimiter = (False if delimiter else True)

            if index == len(args)-1:
                last_arg = args[last_index:len(args)].lstrip().rstrip()
                if last_arg:
                    result.append(last_arg)

        # if one arg
        if not result and args:
            result.append(args)

        return result

    parser = optparse.OptionParser(usage="PyInteractiveHistory [options]")
    parser.add_option('-f',dest='log_filename', metavar='FILE', 
            help="write history to file")
    parser.add_option('-r',dest='raw_format',action='store_true',default=False,
            help="history in raw format")
    parser.add_option('-i',dest='input_only',action='store_true',default=False,
            help="input only")
    parser.add_option('-o',dest='output_only',action='store_true',default=False,
            help="output only")
    try:
        options, _ = parser.parse_args(parse_cmdline(args))

    except SystemExit:
        return

    if options.output_only and options.input_only:
        vim.command('echohl WarningMsg | echo "'
                'Error: mutually exclusive options -i -o" | echohl None')
        return

    history_lines = _interpreter.format_history(
            not options.output_only, not options.input_only, options.raw_format)

    if options.log_filename:
        with open(options.log_filename.strip('"'), 'w') as logfile:
            logfile.write('\n'.join(history_lines))
    else:
        print('\n'.join(history_lines))


def python_autocomplete(text, cmdline, cursorpos):

    completer_ = Completer(_interpreter.locals)

    # NOTE: uncomment this, if you use rlcompleter 
    #import rlcompleter
    #completer_ = rlcompleter.Completer(_interpreter.locals)

    if hasattr(completer_, 'all_completions'):
        return completer_.all_completions(text)
    else:
        completions = []
        comp_append = completions.append
        try:
            for i in xrange(sys.maxint):
                res = completer_.complete(text, i)

                if not res: break

                comp_append(res)
        #XXX workaround for ``notDefined.<tab>``
        except NameError:
            pass
        return completions


