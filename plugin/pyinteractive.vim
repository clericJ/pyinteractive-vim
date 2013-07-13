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

sys.path.append(os.path.join(vim.eval('s:plugin_directory'),
                os.path.normpath('plugin/python')))

import pyinteractive as _pyinteractive
EOF

command PyInteractiveREPL py _pyinteractive.run()
command PyInteractiveRunBuffer py _pyinteractive.execute_buffer()
command -complete=customlist,pyinteractive#PythonAutoCompleteInput -nargs=1 PyInteractiveEval exec 'py _pyinteractive.evaluate_line("""' . escape(<q-args>, "\"'\\"). '""")'
command -complete=file -nargs=* PyInteractiveHistory exec 'py _pyinteractive.show_history("' . escape(<q-args>, "\"'\\"). '")'
command -range PyInteractiveEvalRange <line1>, <line2> py _pyinteractive.evaluate_range()


function! pyinteractive#PythonAutoCompleteInput(begin, cmdline, cursorpos)
    exec 'py result = []'
    exec "py result = _pyinteractive.python_autocomplete('".a:begin."','".a:cmdline."'," a:cursorpos ")"
    py vim.command('let candidates = %r' % result)
    return candidates
endfunction


if g:pyinteractive_add_menu
    nmenu Plugin.PyInteractive.REPL<tab>:PyInteractiveREPL :PyInteractiveREPL<cr>
    nmenu Plugin.PyInteractive.Execute\ Buffer<tab>:PyInteractiveRunBuffer :PyInteractiveRunBuffer<cr>
    nmenu Plugin.PyInteractive.Histoty<tab>:PyInteractiveHistory :PyInteractiveHistory<cr>
    nmenu Plugin.PyInteractive.Histoty\ (Output\ only)<tab>:PyInteractiveHistory\ -o :PyInteractiveHistory -o<cr>

    vmenu PopUp.-Usrsep99- :
    vmenu PopUp.Evaluate\ as\ Python\ code :py _pyinteractive.evaluate_range()<cr>
endif

if g:pyinteractive_add_mappings
   nmap <c-i> :PyInteractiveREPL<cr>
endif

