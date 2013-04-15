#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
from pprint import pformat


try:
    import vim
except ImportError:
    # ignore module (for doctests)
    pass


ShellSSCommand = namedtuple('ShellSSCommand',
                           ('printable',    # bool
                            'match',        # lambda interpreter, source
                            'run'))         # lambda interpreter, source


class ShowDocstringCommand(object):

    printable = True

    def match(self, interpreter, source):
        return (source.rstrip()[-1] == '?')

    def run(self, interpreter, source):
        result = ''
        try:
            result = eval('{0}.__doc__'.format(source[:-1]))

        except Exception:
            pass

        return result


SS_COMMANDS = [
    # use ? for help (max?)
    ShowDocstringCommand(),
    # append input history to current buffer
    ShellSSCommand(
        False,
        (lambda interpreter, source: source.strip() == '%<'),
        (lambda interpreter, source: [vim.current.buffer.append(line)
         for line in interpreter.format_history(include_output=False,raw=True)])
    ), # append output history to current buffer
    ShellSSCommand(
        False,
        (lambda interpreter, source: source.strip() == '%>'),
        (lambda interpreter, source: [vim.current.buffer.append(line)
         for line in interpreter.format_history(include_input=False,raw=True)])
    ), # use "!" for pretty print (e.g. sys.modules!)
    ShellSSCommand(
        True,
        (lambda interpreter, source: source.strip()[-1] == '!'),
        (lambda interpreter, source: pformat(eval(source[:-1], interpreter.locals)))
    ),
]

