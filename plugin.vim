" vimscii — render images as text in-place using img2text.py
" Defaults:
let g:img2text_cmd           = get(g:, 'img2text_cmd', expand('~/.local/bin/img2text.py'))
let g:vimscii_default_mode   = get(g:, 'vimscii_default_mode', 'ascii')
let g:vimscii_default_ramp   = get(g:, 'vimscii_default_ramp', 'dense')   " only for ascii/blocks
let g:vimscii_default_width  = get(g:, 'vimscii_default_width', 120)      " default ~100–120
let g:vimscii_default_height = get(g:, 'vimscii_default_height', 0)       " 0 = fit window
let g:vimscii_default_color  = get(g:, 'vimscii_default_color', 0)        " 0 = no color by default
let g:vimscii_default_cmode  = get(g:, 'vimscii_default_cmode', 'auto')   " auto|fg|bg
let g:vimscii_default_gamma  = get(g:, 'vimscii_default_gamma', 1.0)
let g:vimscii_default_charaspect = get(g:, 'vimscii_default_charaspect', '')
let g:vimscii_default_natural = get(g:, 'vimscii_default_natural', 0)     " 1 = original scale

" --- utilities --------------------------------------------------------------

function! s:Clamp(val, lo, hi) abort
  let v = a:val
  if v < a:lo | let v = a:lo | endif
  if v > a:hi | let v = a:hi | endif
  return v
endfunction

function! s:WinSize() abort
  " portable width/height (no 2-arg max())
  let w = winwidth(0) - 1
  if w < 1 | let w = 1 | endif
  let h = winheight(0) - 1
  if h < 1 | let h = 1 | endif
  return [w, h]
endfunction

function! s:BuildCmd(src, mode, ramp, width, height, color, cmode, gamma, charaspect, natural) abort
  let cmd = 'python3 ' . shellescape(g:img2text_cmd) . ' ' . shellescape(a:src)
  let cmd .= ' --mode ' . a:mode

  if a:mode =~# '^\%(ascii\|blocks\)$' && !empty(a:ramp)
    let cmd .= ' --ramp ' . shellescape(a:ramp)
  endif
  if a:width > 0
    let cmd .= ' --width ' . a:width
  endif
  if a:height > 0
    let cmd .= ' --height ' . a:height
  endif
  if a:color
    let cmd .= ' --color --color-mode ' . a:cmode
  endif

  " ---- FIX: compare gamma as string, not Float
  let gstr = string(a:gamma)
  if gstr !=# '' && gstr !=# '1.0' && gstr !=# '1'
    let cmd .= ' --gamma ' . gstr
  endif

  if a:charaspect !=# ''
    let cmd .= ' --char-aspect ' . a:charaspect
  endif
  if a:natural
    let cmd .= ' --natural'
  endif
  return cmd
endfunction

" Replace whole buffer with render, using defaults (ascii, width ~120, no color)
function! s:RenderHereDefault(file) abort
  let l:src = !empty(a:file) ? a:file : expand('%:p')
  if empty(l:src) || !filereadable(l:src)
    echohl ErrorMsg | echom "Img: no readable file" | echohl None | return
  endif

  setlocal nowrap
  let [wfit, hfit] = s:WinSize()

  " apply default width (cap ~120), default height fit
  let w = g:vimscii_default_width > 0 ? s:Clamp(wfit, 1, g:vimscii_default_width) : wfit
  let h = g:vimscii_default_height > 0 ? s:Clamp(hfit, 1, g:vimscii_default_height) : hfit

  let cmd = s:BuildCmd(l:src,
        \ g:vimscii_default_mode,
        \ g:vimscii_default_ramp,
        \ w, h,
        \ g:vimscii_default_color,
        \ g:vimscii_default_cmode,
        \ g:vimscii_default_gamma,
        \ g:vimscii_default_charaspect,
        \ g:vimscii_default_natural)

  keepjumps %delete _
  execute '0read !' . cmd | 1delete _
  setlocal buftype=nofile bufhidden=wipe noswapfile nomodified readonly
  execute 'file [Image:' . g:vimscii_default_mode . ']'
  normal! ggzt
endfunction

" Replace buffer, passing raw python-style flags (mirrors img2text.py args)
" Usage:
"   :ImgHereArgs --mode braille --width 100 --color --color-mode bg --natural [path]
function! s:RenderHereArgs(raw) abort
  " Parse out an optional path at the end if it exists and is readable; else use %:p.
  let parts = split(a:raw)
  let src = expand('%:p')
  if len(parts) > 0 && filereadable(parts[-1])
    let src = parts[-1]
    call remove(parts, -1)
  endif
  if empty(src) || !filereadable(src)
    echohl ErrorMsg | echom "Img: no readable file" | echohl None | return
  endif

  setlocal nowrap
  let [wfit, hfit] = s:WinSize()
  " If user did not pass --width/--height, clamp to defaults by appending them.
  let have_w = (join(parts) =~# '\v(^| )--width( |$)')
  let have_h = (join(parts) =~# '\v(^| )--height( |$)')
  if !have_w
    let w = g:vimscii_default_width > 0 ? s:Clamp(wfit, 1, g:vimscii_default_width) : wfit
    call add(parts, '--width')
    call add(parts, string(w))
  endif
  if !have_h
    let h = g:vimscii_default_height > 0 ? s:Clamp(hfit, 1, g:vimscii_default_height) : hfit
    call add(parts, '--height')
    call add(parts, string(h))
  endif

  let cmd = 'python3 ' . shellescape(g:img2text_cmd) . ' ' . shellescape(src) . ' ' . join(parts, ' ')
  keepjumps %delete _
  execute '0read !' . cmd | 1delete _
  setlocal buftype=nofile bufhidden=wipe noswapfile nomodified readonly
  execute 'file [Image:args]'
  normal! ggzt
endfunction

" --- public commands --------------------------------------------------------

" Use defaults: ascii, width ~120, fit height, no color
command! -nargs=? ImgHere call s:RenderHereDefault(<q-args>)

" Pass raw flags just like the python CLI:
"   :ImgHereArgs --mode braille --width 100 --color --color-mode bg my.png
command! -nargs=* ImgHereArgs call s:RenderHereArgs(<q-args>)

" (Optional) split preview versions if you ever want them:
" command! -nargs=* ImgSplit execute 'new | setlocal buftype=nofile bufhidden=wipe noswapfile nowrap' | call s:RenderHereDefault(<q-args>)

" Auto-render in-place on open for supported types using defaults
augroup vimscii_autorender
  autocmd!
  autocmd BufReadPost *.png,*.bmp,*.ppm,*.pgm call s:RenderHereDefault(expand('<amatch>'))
augroup END

