" vimscii — render images as text in-place using img2text.py
" Defaults:
let g:img2text_cmd           = get(g:, 'img2text_cmd', expand('~/.local/bin/img2text.py'))
let g:vimscii_default_mode   = get(g:, 'vimscii_default_mode', 'ascii')
let g:vimscii_default_ramp   = get(g:, 'vimscii_default_ramp', 'dense')   " only for ascii/blocks
let g:vimscii_default_width  = get(g:, 'vimscii_default_width', 120)      " default ~100–120
let g:vimscii_default_height = get(g:, 'vimscii_default_height', 0)       " 0 = omit (let aspect auto)
let g:vimscii_default_color  = get(g:, 'vimscii_default_color', 0)        " 0 = no color
let g:vimscii_default_cmode  = get(g:, 'vimscii_default_cmode', 'auto')   " auto|fg|bg
let g:vimscii_default_gamma  = get(g:, 'vimscii_default_gamma', '1.0')    " keep as string to avoid E892
let g:vimscii_default_charaspect = get(g:, 'vimscii_default_charaspect', '')
let g:vimscii_default_natural = get(g:, 'vimscii_default_natural', 0)
let g:vimscii_keep_aspect    = get(g:, 'vimscii_keep_aspect', 1)          " <<< preserve aspect by default

function! s:Clamp(val, lo, hi) abort
  let v = a:val
  if v < a:lo | let v = a:lo | endif
  if v > a:hi | let v = a:hi | endif
  return v
endfunction

function! s:WinSize() abort
  let w = winwidth(0) - 1 | if w < 1 | let w = 1 | endif
  let h = winheight(0) - 1 | if h < 1 | let h = 1 | endif
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
  " >>> Aspect: only pass --height if keep_aspect=0 and height>0
  if !g:vimscii_keep_aspect && a:height > 0
    let cmd .= ' --height ' . a:height
  endif
  if a:color
    let cmd .= ' --color --color-mode ' . a:cmode
  endif
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

" Replace buffer with render, using defaults (ascii, width ~120, no color)
function! s:RenderHereDefault(file) abort
  let l:src = ''
  if !empty(a:file) && filereadable(expand(a:file))
    let l:src = expand(a:file)
  elseif exists('b:vimscii_src') && filereadable(b:vimscii_src)
    let l:src = b:vimscii_src
  else
    let l:src = expand('%:p')
  endif
  if empty(l:src) || !filereadable(l:src)
    echohl ErrorMsg | echom "Img: no readable file (tip: pass a path or run from an image buffer)" | echohl None | return
  endif

  setlocal nowrap
  let [wfit, hfit] = s:WinSize()
  let w = g:vimscii_default_width > 0  ? s:Clamp(wfit, 1, g:vimscii_default_width)   : wfit
  " height will be omitted when keep_aspect=1; else clamp if default_height>0
  let h = g:vimscii_default_height > 0 ? s:Clamp(hfit, 1, g:vimscii_default_height)  : hfit

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
  let b:vimscii_src = l:src
  let g:vimscii_last_src = l:src
  setlocal buftype=nofile bufhidden=wipe noswapfile nomodified readonly
  execute 'file [Image:' . g:vimscii_default_mode . (g:vimscii_keep_aspect ? '' : ':stretch') . ']'
  normal! ggzt
endfunction

" Pass raw python-style flags (mirrors img2text.py). If user omits width/height,
" we auto-add width; height auto-added only when keep_aspect=0.
function! s:RenderHereArgs(raw) abort
  let parts = split(a:raw)
  let src = ''

  if len(parts) > 0
    let last = parts[-1]
    if filereadable(expand(last))
      let src = expand(last)
      call remove(parts, -1)
    endif
  endif

  if empty(src) && exists('b:vimscii_src') && filereadable(b:vimscii_src)
    let src = b:vimscii_src
  endif
  if empty(src) && exists('g:vimscii_last_src') && filereadable(g:vimscii_last_src)
    let src = g:vimscii_last_src
  endif
  if empty(src) && filereadable(expand('%:p'))
    let src = expand('%:p')
  endif
  if empty(src) || !filereadable(src)
    echohl ErrorMsg | echom "Img: no readable file (tip: append a path, e.g. :ImgHereArgs --color ~/pic.png)" | echohl None | return
  endif

  setlocal nowrap
  let [wfit, hfit] = s:WinSize()

  let joined = join(parts)
  let have_w = (joined =~# '\v(^| )--width( |$)')
  let have_h = (joined =~# '\v(^| )--height( |$)')

  if !have_w
    let w = g:vimscii_default_width > 0 ? s:Clamp(wfit, 1, g:vimscii_default_width) : wfit
    call add(parts, '--width')
    call add(parts, string(w))
  endif
  " Only append height when keep_aspect=0 and user didn't pass one
  if !g:vimscii_keep_aspect && !have_h
    let h = g:vimscii_default_height > 0 ? s:Clamp(hfit, 1, g:vimscii_default_height) : hfit
    call add(parts, '--height')
    call add(parts, string(h))
  endif

  let cmd = 'python3 ' . shellescape(g:img2text_cmd) . ' ' . shellescape(src) . ' ' . join(parts, ' ')
  keepjumps %delete _
  execute '0read !' . cmd | 1delete _
  let b:vimscii_src = src
  let g:vimscii_last_src = src
  setlocal buftype=nofile bufhidden=wipe noswapfile nomodified readonly
  execute 'file [Image:args' . (g:vimscii_keep_aspect ? '' : ':stretch') . ']'
  normal! ggzt
endfunction

command! -nargs=? ImgHere     call s:RenderHereDefault(<q-args>)
command! -nargs=* ImgHereArgs call s:RenderHereArgs(<q-args>)

augroup vimscii_autorender
  autocmd!
  autocmd BufReadPost *.png,*.bmp,*.ppm,*.pgm call s:RenderHereDefault(expand('<amatch>'))
augroup END

