" File:     pyinteractive.vim
" Brief:    Python read-eval-print loop inside Vim
" Author:   clericJ (py.cleric at gmail.com)


if v:version < 700
    echoerr 'PyInteractive does not work this version of Vim (' . v:version . ').'
    finish
elseif !has('python')
    finish
elseif exists("g:loaded_PyInteractive")
  finish
endif

let g:loaded_PyInteractive = 1

function! s:initVariable(var, value)
    if !exists(a:var)
        exec 'let ' . a:var . ' = ' . "'" . a:value . "'"
        return 1
    endif
    return 0
endfunction

call s:initVariable("g:pyinteractive_add_menu", 1)
call s:initVariable("g:pyinteractive_add_mappings", 1)
let s:plugin_directory=fnamemodify(expand('<sfile>'), ':p:h:h')

python << EOF
import sys, os, vim

sys.path.append(os.path.join(vim.eval('s:plugin_directory'), os.path.normpath('plugin/python')))

import pyinteractive as _pyinteractive
EOF
command PyInteractiveREPL py _pyinteractive.run()
command PyInteractiveRunBuffer py _pyinteractive.execute_buffer()
command -complete=customlist,pyinteractive#PythonAutoCompleteInput -nargs=1 PyInteractiveEval exec 'py _pyinteractive.evaluate("""' . escape(<q-args>, "\"'\\"). '""")'
command -complete=file -nargs=* PyInteractiveHistory exec 'py _pyinteractive.show_history("' . escape(<q-args>, "\"'\\"). '")'

" Public Interface

function! pyinteractive#PythonAutoCompleteInput(begin, cmdline, cursorpos)
    exec 'py result = []'
    exec "py result = _pyinteractive.python_autocomplete('".a:begin."','".a:cmdline."'," a:cursorpos ")"
    "exec 'py vim.command("let candidates = split(\"%s\")" % "\n".join(result))'
    py vim.command('let candidates = %r' % result)
    "exec 'py vim.command("call confirm(\"%s\")" % str(result))'
    "call candidates(result)
    return candidates
endfunction


function! pyinteractive#EvaluateSelected(type)
    py _pyinteractive.evaluate(vim.current.range[0])
endfunction

if g:pyinteractive_add_menu
    nmenu Plugin.PyInteractive.REPL<tab>:PyInteractiveREPL :PyInteractiveREPL<cr>
    nmenu Plugin.PyInteractive.Execute\ Buffer<tab>:PyInteractiveRunBuffer :PyInteractiveRunBuffer<cr>
    nmenu Plugin.PyInteractive.Histoty<tab>:PyInteractiveHistory :PyInteractiveHistory<cr>
    nmenu Plugin.PyInteractive.Histoty\ (Output\ only)<tab>:PyInteractiveHistory\ -o :PyInteractiveHistory -o<cr>
endif

if g:pyinteractive_add_mappings
   nmap <c-i> :PyInteractiveREPL<cr>
endif

