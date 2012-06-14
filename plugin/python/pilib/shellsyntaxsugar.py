#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
from pprint import pformat


try:
    import vim
except ImportError:
    # ignore module (for doctests)
    pass

# printable: bool
# match: lambda x, y
# run: lambda x, y
ShellSSCommand = namedtuple('ShellSSCommand',
                           ('printable', 'match', 'run'))


SS_COMMANDS = [
    # use ? for help (max?)
    ShellSSCommand(
        True,
        (lambda interpreter, source: source.rstrip()[-1] == '?'),
        (lambda interpreter, source: eval('{0}.__doc__'.format(source[:-1]),
            interpreter.locals))
    ), # append input history to current buffer
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

