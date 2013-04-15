#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import contextlib

@contextlib.contextmanager
def redirect_output(stream):
    """ Utility contextmanager for redirect stdout to stream
        stream - file-like object (e.g. StringIO)

        Usage:
            >>> stream = StringIO()
            >>> with redirect_output(stream):
            ...     print("Hello")
            ...
            >>> stream.getvalue()
            'Hello\\n'
    """
    old = sys.stdout
    sys.stdout = stream
    try:
        yield

    finally:
        sys.stdout = old


@contextlib.contextmanager
def vim_input_guard():
    """ Contextmanager for vim safe input
    """
    import vim
    vim.command('call inputsave()')
    try:
        yield

    finally:
        vim.command('call inputrestore()')


class dynamicmethod(object):
    """Class implements decorator for making instance methods

        Example:
            >>> class Dummy(object): pass
            >>> dum = Dummy()

            >>> @dynamicmethod(dum)
            ... def say_hello(self):
            ...    return 'hello'

            >>> dum.say_hello()
            'hello'
    """

    def __init__(self, instance):
        self.instance = instance


    def __call__(self, func):

        # get instancemethod descriptor
        im_descriptor = self.__init__.__class__

        method = im_descriptor(func, self.instance, self.instance.__class__)
        setattr(self.instance, func.__name__, method)

        return method

