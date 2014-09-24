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

function! s:worksheet_start()
	let inputBuf = bufnr('%')
    set scrollbind
    rightbelow vnew
    vertical resize 50
    setlocal nonumber
    setlocal nowrap
	let outputBuf = bufnr('%')
    set scrollbind
    wincmd h

py<<EOF
input_buf = int(vim.eval('inputBuf'))
output_buf = int(vim.eval('outputBuf'))
worksheet = WorksheetEvalCommand(input_buf, output_buf).run()
EOF
    set nomodifiable
endfunction

command! Worksheet call s:worksheet_start()
nmap <Leader>ws :Worksheet<CR>
