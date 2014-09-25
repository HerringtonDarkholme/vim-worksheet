" Bootstrap
if exists('g:loaded_worksheet') || &cp
    finish
endif
let g:loaded_worksheet = 1

" configure Python version
if !exists('g:worksheetPyVersion')
    let g:worksheetPyVersion = 2
endif
if g:worksheetPyVersion == 3
    let s:py = 'py3 '
    let s:pyfile = 'py3file '
else
    let s:py = 'py '
    let s:pyfile = 'pyfile '
endif

" load python
let s:SourcePath=expand('<sfile>:p:h')
exec s:py . 'import sys, vim'
exec s:py . 'source_path = vim.eval("s:SourcePath")'
exec s:py . 'sys.path.append(source_path)'
exec s:pyfile . s:SourcePath . '/worksheet.py'

" opend buffer
let s:opend = {}

function! s:worksheet_start()
    let inputBuf = bufnr('%')
    if exists('s:opend['. inputBuf .']')
        echo 'worksheet already started'
        return 0
    else
        let s:opend[inputBuf] = 1
    endif

    "bind scrolling
    set scrollbind
    "open new window rightside and
    rightbelow vnew
    vertical resize 40
    setlocal nonumber
    setlocal nowrap
    let outputBuf = bufnr('%')
    set scrollbind
    " come back to source buffer
    wincmd h

py<<EOF
input_buf = int(vim.eval('inputBuf'))
output_buf = int(vim.eval('outputBuf'))
if not Cache.get(input_buf):
    worksheet = WorksheetCommand(input_buf, output_buf)
    worksheet.make_sheet()
    vim.command('call s:worksheet_bind()')
else:
    vim.command('echo')
EOF
endfunction

function! s:worksheet_eval()
    let inputBuf = bufnr('%')
py<<EOF
input_buf = int(vim.eval('inputBuf'))
worksheet = Cache.get(input_buf)
if not worksheet:
    print('No worksheet found for buffer')
    vim.eval('return 1')
else:
    worksheet.make_sheet()
EOF
endfunction

function! s:worksheet_end()
    let inputBuf = bufnr('%')
    if exists('s:opend['. inputBuf .']')
        unlet s:opend[inputBuf]
    else
        echo 'No worksheet found for buffer'
        return 1
    endif
py<<EOF
input_buf = int(vim.eval('inputBuf'))
worksheet = Cache.get(input_buf)
if not worksheet:
    print('No worksheet found for buffer')
else:
    worksheet.end_session()
    vim.command('call s:worksheet_unbind()')
EOF
endfunction

function! s:worksheet_clean()
    let inputBuf = bufnr('%')
py<<EOF
input_buf = int(vim.eval('inputBuf'))
worksheet = Cache.get(input_buf)
if not worksheet:
    print('No worksheet found for buffer')
else:
    worksheet.remove_previous_results()
EOF
    return 0
endfunction

function! s:worksheet_bind()
    command-buffer WorksheetEval call s:worksheet_eval()
    command-buffer WorksheetEnd call s:worksheet_end()
    command-buffer WorksheetClean call s:worksheet_clean()
    nnoremap <buffer> <leader>wc :WorksheetClean<CR>
    nnoremap <buffer> <leader>we :WorksheetEnd<CR>
    augroup worksheetgroup
        autocmd BufWritePre <buffer> WorksheetClean
        autocmd BufWritePost <buffer> WorksheetEval
        autocmd BufLeave <buffer> WorksheetEnd
    augroup END
endfunction

function! s:worksheet_unbind()
    delcommand WorksheetEval
    delcommand WorksheetEnd
    delcommand WorksheetClean
    nunmap <buffer> <leader>wc
    nunmap <buffer> <leader>we
    augroup worksheetgroup
        autocmd!
    augroup END

endfunction

command WorksheetStart call s:worksheet_start()
nmap <Leader>ws :WorksheetStart<CR>
