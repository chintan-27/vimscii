# vimscii
View images directly inside Vim — using only Python and text.

`vimscii` converts images (PNG, BMP, PPM/PGM) into ASCII, Braille, or block characters — displayed directly in your terminal Vim or Neovim.  
No plugins, no GUI, no dependencies.

---

## Features
- Works in plain Vim or Neovim, even over SSH.
- Supports **color** (`--color`, 24-bit ANSI).
- Multiple modes: `braille`, `half`, `ascii`, `blocks`.
- Scales automatically for terminal aspect ratio.
- Pure Python — no external libraries or binaries.

---

## Installation

### Linux / macOS

```bash
# Install the converter script
mkdir -p ~/.local/bin
wget -O ~/.local/bin/img2text.py https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py
chmod +x ~/.local/bin/img2text.py

# Add minimal Vim integration
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
EOF
````

### Windows (PowerShell)

```powershell
# Install the script
New-Item -ItemType Directory -Force $env:USERPROFILE\vimscii | Out-Null
Invoke-WebRequest https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py -OutFile $env:USERPROFILE\vimscii\img2text.py

# Add a small Vim plugin (PowerShell syntax)
$pluginDir = "$env:USERPROFILE\vimfiles\plugin"
New-Item -ItemType Directory -Force $pluginDir | Out-Null
@"
let g:img2text_cmd = expand('$env:USERPROFILE/vimscii/img2text.py')
command! -nargs=? Img execute '!python ' . shellescape(g:img2text_cmd) . ' ' . shellescape(expand("<args>"))
"@ | Set-Content "$pluginDir\vimscii.vim"
```

---

## Usage

Once installed, simply open any image in Vim or Neovim:

```bash
vi image.png
```

or from within Vim, use commands:

```
:Img
:Img path/to/image.png
:ImgWith ascii dense
:ImgWith blocks blocks
:ImgWith half
```

---

## Command-line mode

You can also run it directly in a terminal:

```bash
python3 img2text.py image.png --mode braille --width 100 --color
python3 img2text.py image.png --mode ascii --ramp dense --width 120 --color
python3 img2text.py image.png --mode blocks --ramp blocks --width 100 --color --color-mode bg
python3 img2text.py image.png --mode half --width 120 --color --color-mode auto
```

---

## Options

| Option                 | Description                                                         |
| ---------------------- | ------------------------------------------------------------------- |
| `--mode`               | One of `braille`, `half`, `ascii`, `blocks`                         |
| `--ramp`               | Choose character ramp (`dense`, `blocks`, `dots`, or custom string) |
| `--width` / `--height` | Output size in text cells                                           |
| `--color`              | Enable 24-bit color output                                          |
| `--color-mode`         | `auto`, `fg`, or `bg` (brightness-adaptive by default)              |
| `--gamma`              | Adjust brightness curve (default 1.0)                               |

---

## Terminal setup for color

Ensure your terminal supports 24-bit (truecolor):

```bash
printf "\x1b[38;2;255;0;0mRED \x1b[38;2;0;255;0mGREEN \x1b[38;2;0;0;255mBLUE\x1b[0m\n"
```

If all three words show in different colors, truecolor is enabled.
For tmux users:

```
set -g default-terminal "tmux-256color"
set -as terminal-features ',xterm-256color:RGB'
```

In Vim/Neovim:

```
:set termguicolors
```

---

## Supported formats

* PNG (non-interlaced)
* BMP (24/32-bit)
* PPM / PGM (P6 / P5)

---

## Example workflow

```bash
vi photo.png       # opens photo.png as ASCII art
:ImgWith ascii dense
:ImgWith blocks blocks
```

---

## License

MIT License — open for modification and reuse.



