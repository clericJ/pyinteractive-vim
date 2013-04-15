#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tokenize, token
from StringIO import StringIO


NAMESPACE_DELIMITER = '.'
ASSIGNMENT_OPS = ['=', '+=', '-=', '*=', '/=']


def _debug_tokeninfo(token_):
    """ _debug_tokeninfo(token_: tuple) -> str
    """
    type_, tok, (srow, scol), (erow, ecol), line = token_
    return '''\
            type:       {0}
            token:      [{1}]
            srow-scol:  ({2},{3})
            erow-ecol:  ({4},{5})
            line:       [{6}]
            '''.format(token.tok_name[type_], tok, srow, scol, erow, ecol, line)


def _tokenize(text):
    """ _tokenize(text: str) -> list
        Tokenize python source code
    """
    tokenized = []
    try:
        token_info = tokenize.tokenize(StringIO(text).readline,
            (lambda type_, token, (srow, scol), (erow, ecol), line:
                tokenized.append((type_,token,(srow,scol),(erow,ecol),line))))

    except tokenize.TokenError:
        pass

    return tokenized


def _filter_candidates(begin, candidates):
    """ _filter_candidates(begin: str, candidates: iterable) -> iterable
        Utility function helps in autocomplete

        Usage:
            >>> _filter_candidates('abr', ['abbra_cadabra', 'abbreviations'])
            []
            >>> _filter_candidates('abbr', ['abbra_cadabra', 'abbreviations'])
            ['abbra_cadabra', 'abbreviations']
            >>> _filter_candidates('he', ['apply', 'help', 'bin'])
            ['help']
            >>> _filter_candidates('_', ['a_b', 'c_d', '_e'])
            ['_e']
            >>> _filter_candidates('_', ['a_', '_b', 'c_d', '_e'])
            ['_b', '_e']
    """
    result = []
    for candidate in candidates:
        if len(candidate) < len(begin):
            continue
        if candidate[0:len(begin)] == begin:
            result.append(candidate)
    #vim.command('call confirm("begin:\n%s\ncandidates:\n%s\nresult:%s\n", "Close")' % (begin, candidates, result))
    return result


def _get_inner_namespace(text):
    """ _get_inner_namespace(text: str) -> list
    For 'mod1.func("_", [mod2.class1.__' texting return 'mod2.class1'

    Usage:
        >>> _get_inner_namespace('mod1.func("_",[mod2.class1.__')
        'mod2.class1'
        >>> _get_inner_namespace('mod1.func("_",[mod2.class1.')
        'mod2.class1'
        >>> _get_inner_namespace('mod1.func("_",(mod2.class1_')
        'mod2'
        >>> _get_inner_namespace('help(  vars.')
        'vars'
        >>> _get_inner_namespace('help(  vars._')
        'vars'
        >>> _get_inner_namespace('vars._')
        'vars'
        >>> _get_inner_namespace('vars.')
        'vars'
        >>> _get_inner_namespace('vars')
        ''
        >>> _get_inner_namespace('s = str.low')
        'str'
    """
    tokenized = _tokenize(text)

    if any(filter((lambda x: x[0] == tokenize.OP and x[1] in ASSIGNMENT_OPS),
       tokenized)): tokenized = tokenized[:-1]

    for token_info in reversed(tokenized):
        if(token_info[0] == tokenize.OP and token_info[1] == NAMESPACE_DELIMITER
            or token_info[0] == tokenize.NAME):
            continue
        # sys.std|...
        # help(sys.std|...
        last = tokenized[-1]
        if (last[0] == tokenize.NAME or (last[0] == tokenize.ENDMARKER
            and len(tokenized) > 1)):

            lastop_info = _get_lastop_info(tokenized)
            if not lastop_info:
                return ''
            return text[token_info[3][1]:lastop_info[2][1]].lstrip()
        # sys.|...
        # help(sys.|...
        else:
            return text[token_info[3][1]:len(text)-1].lstrip()
    return ''


def _get_lastop_info(tokenized):
    """  _get_lastop_info(tokenized: list) -> iterable or None
        Return token info for last OP or None if OP not exist
    """
    for token_info in reversed(tokenized):
        if token_info[0] == tokenize.OP:
            return token_info
    return None


def _get_last_meaning_token_info(tokenized):
    """ _get_last_name_token(tokenized: list) -> iterable or None
        Return last meaning token (NAME, OP...) in token list if exists or None
        Doctest:
            >>> tokens = [\
                    (5, ' ', (1,0),(1,1),'abbr'),\
                    (1, 'abbr', (1,1),(1,5),'abbr'),\
                    (6, '', (2,0),(2,0),'abbr'),\
                    (0, '', (2,0),(2,0),'abbr')]
            >>> tokens[-3] == _get_last_meaning_token_info(tokens)
            True
            >>> _get_last_meaning_token_info([(0, '', (1,0),(1,0),'')]) is None
            True
    """
    last = tokenized[-1]
    if last[0] == tokenize.ENDMARKER:
        if len(tokenized) > 1:
            # >>> boo
            #     NAME-ENDMARKER
            #       ^---<------<----
            last = tokenized[-2]
            if len(tokenized) > 2 and last[0] == tokenize.DEDENT:
                # >>>        boo
                #    INDENT-NAME-DEDENT-ENDMARKER
                #             ^---<------<----
                last = tokenized[-3]
        else: # |...
            return None

    return last


def _exclude_private_members(candidates):
    """ _exclude_private_members(candidates: iterable) -> iterable
    Skip items begins  with '_'
        Usage:
            >>> attribs = ['_a', 'b', '_c', 'd_', 'e_f']
            >>> _exclude_private_members(attribs)
            ['b', 'd_', 'e_f']
    """
    return filter(lambda string: string[:1] != '_', candidates)



class Completer(object):

    def __init__(self, namespace=None):

        if namespace and not isinstance(namespace, dict):
            raise TypeError,'Namespace must be a dictionary'

        if namespace is None:
            namespace = {}

        self.namespace = namespace
        self.namespace.update(__builtins__ if isinstance(__builtins__, dict)
                              else __builtins__.__dict__)


    def complete(self, text, state):
        completions = self.all_completions(text)
        try:
            return completions[state]
        except IndexError:
            return None


    # hel| divmod?
    # import StringIO
    # s=StringIO.S<tab> ERROR dir takes no keyword arguments
    # dir('s=StringIO.S') !!!
    def all_completions(self, text, cmdline='', cursorpos=0):
        """ all_completions(text: str) -> list
            Uses for vim command autocompletion
            Usage:
                # setup
                >>> import pythonshell
                >>> _interpreter = pythonshell.VimInterpreter()
                >>> _interpreter.locals['sys'] = __import__('sys')
                >>> _interpreter.locals['dt'] = __import__('datetime')
                >>> _compl = Completer(_interpreter.locals)
                >>> sys_names = _exclude_private_members(dir(_interpreter.locals['sys']))
                >>> dt_names = _exclude_private_members(dir(_interpreter.locals['dt']))

                >>> _interpreter.locals['abbra_cadabra'] = None
                >>> _compl.all_completions('abbr', 'abbr', 4)
                ['abbra_cadabra']
                >>> _compl.all_completions('abbre', 'abbre', 5)
                []
                >>> _interpreter.locals['abbreviations'] = None
                >>> _compl.all_completions('abbr', 'abbr', 4)
                ['abbreviations', 'abbra_cadabra']

                >>> _compl.all_completions('abbre', 'abbre', 5)
                ['abbreviations']
                >>> ['sys.' + item for item in sys_names] \
                        == _compl.all_completions('sys.', 'sys.', 4)
                True
                >>> (['help(sys.' + item for item in sys_names] \
                        == _compl.all_completions('help(sys.', 'help(sys.', 9))
                True
                >>> _compl.all_completions('help(sys.stdou', 'help(sys.stdou', 14)
                ['help(sys.stdout']

                >>> ['dt.' + item for item in dt_names] \
                        == _compl.all_completions('dt.', 'dt.', 3) #XXX
                True
                >>> _compl.all_completions('help(abbr', 'help(abbr', 9)
                ['help(abbreviations', 'help(abbra_cadabra']

                >>> _compl.all_completions('help(abbra', 'help(abbra', 10)
                ['help(abbra_cadabra']

                >>> _compl.all_completions('help(abbr.', 'help(abbr.', 10)
                []
                >>> _compl.all_completions('help( abbra', 'help( abbra', 11)
                ['help( abbra_cadabra']
                >>> _compl.all_completions(' abbr', ' abbr', 5)
                [' abbreviations', ' abbra_cadabra']
        """
        #vim.command('call confirm("<%s>\n<%s>\n<%i>", %i)' % (text,cmdline,cursorpos,cursorpos))

        candidates = []
        tokenized = _tokenize(text)
        lastop_info = _get_lastop_info(tokenized)
        last = _get_last_meaning_token_info(tokenized)
        # >>> |...
        # >>>   |...
        if last is None:
            return _exclude_private_members(text + c for c in list(self.namespace.keys()))

        inner = _get_inner_namespace(text)
        if last[0] == tokenize.NAME:
            # sys.std|...
            # help(sys.std|...
            if lastop_info and lastop_info[1] == NAMESPACE_DELIMITER:
                if not inner:
                    return []
                try:
                    candidates = eval('dir({0})'.format(inner), self.namespace)
                except (NameError, SyntaxError):
                    #vim.command('call confirm("debug: syntax or name error#1\n<%s>\n<%s>")' % (text, inner))
                    return []

                candidates = _filter_candidates(last[1], candidates)
                return [text[:-len(last[1])] + item for item in candidates]
            # help(bu|...
            elif lastop_info:
                candidates = _filter_candidates(last[1], list(self.namespace.keys()))
                return [text[:-len(last[1])] + item for item in candidates]
            # __|...
            else:
                # >>> INDENT bo|...
                if tokenized[0][0] == token.INDENT:
                    #vim.command('call confirm("!!")')
                    return [tokenized[0][1] + c for c in _filter_candidates(last[1],
                        list(self.namespace.keys()))]
                # boo|...
                else:
                    return _filter_candidates(last[1], list(self.namespace.keys()))

        elif last[0] == tokenize.OP:
            # sys.|...
            # help(sys.|...
            if last[1] == NAMESPACE_DELIMITER:
                if not inner:
                    return []
                try:
                    #vim.command('call confirm("debug: %s")'%_get_inner_namespace(text))
                    candidates = eval('dir({0})'.format(inner), self.namespace)

                    candidates = _exclude_private_members(candidates)
                except (NameError, SyntaxError):
                    #vim.command('call confirm("debug: syntax or name error#2\n%s")' % (text[:-1]))
                    return []

            else: # help(|...
                candidates = _exclude_private_members(list(self.namespace.keys()))

        return [text + item for item in candidates]



def _test():
    import doctest
    doctest.testmod()


if(__name__ in ('__main__', '__console__')):
    _test()
