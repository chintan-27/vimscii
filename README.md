# vimscii
View images directly inside Vim/Neovim — ASCII, Braille, and block characters — using only Python’s standard library.

`vimscii` converts PNG/BMP/PPM/PGM into text art and shows it in a scratch buffer. No GUI, no external libraries.

---

## Features
- Works in plain Vim or Neovim (even over SSH).
- Modes: `braille`, `half`, `ascii`, `blocks`.
- Optional 24-bit color (`--color`, with `--color-mode auto|fg|bg`).
- Pure Python, single file, no dependencies.

---

## Installation

> Replace the GitHub URL if your repository path differs.

### Linux / macOS (Vim)

```bash
# 1) Install the converter script
mkdir -p ~/.local/bin
wget -O ~/.local/bin/img2text.py https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py
chmod +x ~/.local/bin/img2text.py

# 2) Install the Vim plugin (defines :Img and :ImgWith)
mkdir -p ~/.vim/pack/plugins/start/vimscii
cat > ~/.vim/pack/plugins/start/vimscii/plugin.vim <<'EOF'
let g:img2text_cmd = expand('~/.local/bin/img2text.py')

function! s:ImgRun(mode, ramp, file) abort
  botright new
  setlocal buftype=nofile bufhidden=wipe noswapfile nowrap nonumber norelativenumber
  let l:w = max(1, winwidth(0) - 1)
  let l:f = !empty(a:file) ? a:file : expand('%:p')
  if empty(l:f) || !filereadable(l:f)
    echohl ErrorMsg | echom "Img: no readable file" | echohl None | bwipeout! | return
  endif
  let l:cmd = 'python3 ' . shellescape(g:img2text_cmd) . ' ' . shellescape(l:f)
  let l:cmd .= ' --mode ' . a:mode . ' --width ' . l:w
  if a:mode =~# '^\%(ascii\|blocks\)$' && !empty(a:ramp)
    let l:cmd .= ' --ramp ' . shellescape(a:ramp)
  endif
  execute '0read !' . l:cmd
  normal! gg
  execute 'file [Image:' . a:mode . ']'
endfunction

command! -nargs=? Img call s:ImgRun('braille', '', <q-args>)
command! -nargs=* ImgWith call s:ImgWith(<q-args>)
function! s:ImgWith(args) abort
  let l:parts = split(a:args)
  let l:mode  = len(l:parts) > 0 ? l:parts[0] : 'braille'
  let l:ramp  = (l:mode ==# 'ascii' || l:mode ==# 'blocks') && len(l:parts) > 1 ? l:parts[1] : ''
  let l:file  = (l:mode ==# 'ascii' || l:mode ==# 'blocks') ? (len(l:parts) > 2 ? l:parts[2] : '') : (len(l:parts) > 1 ? l:parts[1] : '')
  call s:ImgRun(l:mode, l:ramp, l:file)
endfunction

" Auto-render supported image types on open
augroup vimscii_autorender
  autocmd!
  autocmd BufReadPost *.png,*.bmp,*.ppm,*.pgm Img
augroup END
EOF

# 3) Ensure Vim loads user packages
grep -q 'set packpath^=~/.vim' ~/.vimrc || echo 'set packpath^=~/.vim' >> ~/.vimrc
````

### Linux / macOS (Neovim)

```bash
# 1) Use the same script
mkdir -p ~/.local/bin
wget -O ~/.local/bin/img2text.py https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py
chmod +x ~/.local/bin/img2text.py

# 2) Neovim package path
mkdir -p ~/.local/share/nvim/site/pack/plugins/start/vimscii
cat > ~/.local/share/nvim/site/pack/plugins/start/vimscii/plugin.vim <<'EOF'
let g:img2text_cmd = expand('~/.local/bin/img2text.py')

function! s:ImgRun(mode, ramp, file) abort
  botright new
  setlocal buftype=nofile bufhidden=wipe noswapfile nowrap nonumber norelativenumber
  let l:w = max(1, winwidth(0) - 1)
  let l:f = !empty(a:file) ? a:file : expand('%:p')
  if empty(l:f) || !filereadable(l:f)
    echohl ErrorMsg | echom "Img: no readable file" | echohl None | bwipeout! | return
  endif
  let l:cmd = 'python3 ' . shellescape(g:img2text_cmd) . ' ' . shellescape(l:f)
  let l:cmd .= ' --mode ' . a:mode . ' --width ' . l:w
  if a:mode =~# '^\%(ascii\|blocks\)$' && !empty(a:ramp)
    let l:cmd .= ' --ramp ' . shellescape(a:ramp)
  endif
  execute '0read !' . l:cmd
  normal! gg
  execute 'file [Image:' . a:mode . ']'
endfunction

command! -nargs=? Img call s:ImgRun('braille', '', <q-args>)
command! -nargs=* ImgWith call s:ImgWith(<q-args>)
function! s:ImgWith(args) abort
  let l:parts = split(a:args)
  let l:mode  = len(l:parts) > 0 ? l:parts[0] : 'braille'
  let l:ramp  = (l:mode ==# 'ascii' || l:mode ==# 'blocks') && len(l:parts) > 1 ? l:parts[1] : ''
  let l:file  = (l:mode ==# 'ascii' || l:mode ==# 'blocks') ? (len(l:parts) > 2 ? l:parts[2] : '') : (len(l:parts) > 1 ? l:parts[1] : '')
  call s:ImgRun(l:mode, l:ramp, l:file)
endfunction

augroup vimscii_autorender
  autocmd!
  autocmd BufReadPost *.png,*.bmp,*.ppm,*.pgm Img
augroup END
EOF
```

### Windows (PowerShell, Vim)

```powershell
# 1) Script
New-Item -ItemType Directory -Force $env:USERPROFILE\bin | Out-Null
Invoke-WebRequest https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py -OutFile $env:USERPROFILE\bin\img2text.py

# 2) Vim plugin (vimfiles path on Windows)
$pluginDir = "$env:USERPROFILE\vimfiles\plugin"
New-Item -ItemType Directory -Force $pluginDir | Out-Null
@"
let g:img2text_cmd = expand('$env:USERPROFILE/bin/img2text.py')
command! -nargs=? Img execute 'new | setlocal buftype=nofile bufhidden=wipe noswapfile nowrap | 0read !python ' . shellescape(g:img2text_cmd) . ' ' . shellescape(expand("<args>"))
"@ | Set-Content "$pluginDir\vimscii.vim"
```

---

## Usage

Open an image and it auto-renders (Vim/Neovim):

```bash
vi image.png
```

Manual commands (inside Vim/Neovim):

```
:Img                          " render current file (braille)
:Img path/to/image.png        " render a path
:ImgWith ascii dense          " ascii mode with dense ramp
:ImgWith blocks blocks        " block shades
:ImgWith half                 " half-block mode
```

Command line:

```bash
python3 img2text.py image.png --mode braille --width 100 --color
python3 img2text.py image.png --mode ascii --ramp dense --width 120 --color
python3 img2text.py image.png --mode blocks --ramp blocks --width 100 --color --color-mode bg
python3 img2text.py image.png --mode half --width 120 --color --color-mode auto
```

---

## Tips

* Ensure truecolor support:

  ```bash
  printf "\x1b[38;2;255;0;0mRED \x1b[38;2;0;255;0mGREEN \x1b[38;2;0;0;255mBLUE\x1b[0m\n"
  ```
* tmux:

  ```
  set -g default-terminal "tmux-256color"
  set -as terminal-features ',xterm-256color:RGB'
  ```
* Vim/Neovim:

  ```
  :set termguicolors
  ```
* PNGs must be non-interlaced (Adam7 isn’t supported). Re-save if needed:

  * macOS: `sips -s format png image.png --out fixed.png`
  * ImageMagick: `convert image.png -interlace none fixed.png`

---

## Troubleshooting

* `E492: Not an editor command: Img`
  Run `:scriptnames` and confirm a line ends with `vimscii/plugin.vim`.
  For Vim, ensure `set packpath^=~/.vim` is in `~/.vimrc`.
  For Neovim, the plugin must be under `~/.local/share/nvim/site/pack/...`.

---

## License

MIT
