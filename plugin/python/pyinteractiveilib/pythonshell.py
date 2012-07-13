#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import print_function

import sys
from code import InteractiveConsole
from StringIO import StringIO

from util import redirect_output, vim_input_guard, dynamicmethod
from shellsyntaxsugar import SS_COMMANDS

try:
    import vim
except ImportError:
    # ignore module (for doctests)
    pass


PROMPT = (sys.ps1 if hasattr(sys, 'ps1') else '>>> ')
MORE   = (sys.ps2 if hasattr(sys, 'ps2') else '... ')


HIST_IN_PATTERN  = " in[{0}]: "
HIST_OUT_PATTERN = "out[{0}]: "

# history flags
IN_FLAG  = 0
OUT_FLAG = 1

# indent 4 spaces
TABSTOP  = 4

class VimInterpreter(InteractiveConsole):

    def __init__(self, locals=None, filename="<console>"):

        if locals is None:
            locals = {'__name__': '__console__', '__doc__': None}
            locals['_interpreter'] = self
            locals['sys'] = sys
            if 'vim' in globals():
                locals['vim'] = vim

        InteractiveConsole.__init__(self, locals, filename)

        # history consists of list of pairs [(FLAG, record), ...]
        # flag is IN_FLAG or OUT_FLAG
        # record a string containing history line
        self.history = []


    def push(self, line):
        """ push(line: str) -> int
            See InteractiveConsole.push documentation
        """
        result = 0
        stream = StringIO()
        stdout = sys.stdout

        # replace StringIO.write method in stream
        @dynamicmethod(stream)
        def write(this, data):
            stdout.write(data)
            return StringIO.write(this, data)

        self.history.append((IN_FLAG, line))
        with redirect_output(stream):
            result = InteractiveConsole.push(self, line)

        output = stream.getvalue()
        if output.strip():
            self.history.append((OUT_FLAG, output))

        return result


    def parse_ss(self, text):
        """  parse_ss(text: str) -> bool
            if syntax sugar exists in code return True else False
        """
        for command in SS_COMMANDS:
            if command.match(self, text):
                result = command.run(self, text)
                if command.printable:
                    print(result)

                return True
        return False


    def _display_banner(self, banner):
        if banner:
            InteractiveConsole.push(self, 'print({0})'.format(banner))
            return

        vinfo = sys.version_info
        vim.command('echohl StatusLine | echo "'
                'Python {0}.{1}.{2} " | echohl None'.format(
                vinfo.major, vinfo.minor, vinfo.micro))


    def interact(self, banner=None):
        """ Run python read-eval-print loop. Press <ESC> to exit
        """
        self._display_banner(banner)

        while True:
            with vim_input_guard():
                text = vim.eval(u'input("{0}","","customlist,'
                        'pyinteractive#PythonAutoCompleteInput")'.format(PROMPT))

            vim.command('echo "\r"')
            if text is None:
                break

            elif (text.strip() != '') and self.parse_ss(text) is True:
               continue

            # autoident
            indent = (' ' * TABSTOP)
            indent_level = 1
            autoindent = (lambda level: indent * level if level > 0 else '')

            while self.push(text):
                with vim_input_guard():
                    text = vim.eval(
                        u'input("{0}","{1}","customlist,'
                                'pyinteractive#PythonAutoCompleteInput")'.format(
                                 MORE, autoindent(indent_level)) )

                vim.command('echo "\r"')
                if text is None:
                    return

                # TODO: hardcoded condition
                if text.rstrip().endswith(':'):
                    indent_level += 1

                elif text.isspace():
                    indent_level = (0 if indent_level==0 else indent_level-1)


    def evaluate(self, source):
        """ Evaluate python code in interpreter
            source - python code (str)
        """
        ### FIXME: indent error in multiline code
        for line in source.splitlines():
            if(line.strip() != ''):
                self.push(line)

        self.push('\n')


    def execute_buffer(self):
        """ Run current buffer in interpreter
        """
        buffername = vim.current.buffer.name
        if buffername is None:
            buffername = '<empty>'

        source = ('\n'.join(vim.current.buffer))
        code = compile(source, buffername, 'exec')
        self.runcode(code)


    def format_history(self, include_input=True, include_output=True, raw=False):
        """ Format and return input/output history in current
            session (list of strings)
            include_input (bool) if True (by default) intput history
              added to result
            include_output (bool) if True (by default) output history
              added to result
            raw (bool) if True extra info not appended to result

        Usage:
            >>> vi = VimInterpreter()
            >>> vi.history = [\
            (IN_FLAG, 'print("hello")'),(OUT_FLAG, "hello"),\
            (IN_FLAG, 'print("world")'),(OUT_FLAG, "world")]

            >>> # >>>open("C:/h.txt","w").write(str(vi.format_history(raw=True)))

            >>> vi.format_history()
            [' in[1]: print("hello")', 'out[1]: hello', ' in[2]: print("world")', 'out[2]: world']

            >>> vi.format_history(include_input=False)
            ['out[1]: hello', 'out[2]: world']

            >>> vi.format_history(include_output=False)
            [' in[1]: print("hello")', ' in[2]: print("world")']

            >>> vi.format_history(raw=True)
            ['print("hello")', 'hello', 'print("world")', 'world']

            >>> vi.history = [(IN_FLAG, 'def test(): print 1,2,3'), (OUT_FLAG, '1, 2, 3')]
            >>> vi.format_history(raw=True)
            ['def test(): print 1,2,3', '1, 2, 3']

            >>> vi.format_history()
            [' in[1]: def test(): print 1,2,3', 'out[1]: 1, 2, 3']
        """
        result = []
        lineno_map = {IN_FLAG: 1, OUT_FLAG: 1}
        flags_case = {IN_FLAG: HIST_IN_PATTERN, OUT_FLAG: HIST_OUT_PATTERN}

        format_line = (lambda flag, line:
            (line if raw else (flags_case[flag].format(lineno_map[flag])+line)))

        for flag, line in self.history:
            if line == '\n':
                continue

            if((flag == IN_FLAG and include_input) or
                flag == OUT_FLAG and include_output):

                result.append(format_line(flag, line))
                lineno_map[flag] += 1

        return result


    def clear_history(self):
        """ Clear all history items
        """
        self.history = []



def _test():
    import doctest
    doctest.testmod()


if(__name__ in ('__main__', '__console__')):
    _test()
