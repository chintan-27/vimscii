# vimscii

**View images directly in classic Vim**, converted to ASCII, Braille, or Block art — no GUI, no plugins, no external dependencies.

---

## Requirements

- **Python 3** (must be available as `python3`)
- **Vim 8.0+** (tested with Vim 9.1)
- UTF-8 capable terminal (for Braille and blocks)
- Monospaced font recommended

Supported image formats:
- PNG (8-bit non-interlaced)
- BMP (24/32-bit)
- PPM / PGM (binary P6 / P5)

---

## Installation

### Linux
```bash
# Install Python (if not already)
sudo apt install -y python3 wget

# Get the converter script
mkdir -p ~/.local/bin
wget -O ~/.local/bin/img2text.py https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py
chmod +x ~/.local/bin/img2text.py

# Add Vim plugin
mkdir -p ~/.vim/pack/plugins/start/vimscii
wget -O ~/.vim/pack/plugins/start/vimscii/plugin.vim https://raw.githubusercontent.com/chintan-27/vimscii/main/plugin.vim

# Ensure Vim loads from ~/.vim
grep -q 'set packpath^=~/.vim' ~/.vimrc 2>/dev/null || echo 'set packpath^=~/.vim' >> ~/.vimrc
````

---

### macOS

```bash
# Install Python if needed
brew install python wget

# Fetch the converter and plugin
mkdir -p ~/.local/bin
wget -O ~/.local/bin/img2text.py https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py
chmod +x ~/.local/bin/img2text.py

mkdir -p ~/.vim/pack/plugins/start/vimscii
wget -O ~/.vim/pack/plugins/start/vimscii/plugin.vim https://raw.githubusercontent.com/chintan-27/vimscii/main/plugin.vim

# Ensure ~/.vim is in Vim's packpath
grep -q 'set packpath^=~/.vim' ~/.vimrc 2>/dev/null || echo 'set packpath^=~/.vim' >> ~/.vimrc
```

---

### Windows (PowerShell)

```powershell
# Create folders
mkdir "$env:USERPROFILE\.local\bin" -Force
mkdir "$env:USERPROFILE\.vim\pack\plugins\start\vimscii" -Force

# Download files
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/chintan-27/vimscii/main/img2text.py" -OutFile "$env:USERPROFILE\.local\bin\img2text.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/chintan-27/vimscii/main/plugin.vim" -OutFile "$env:USERPROFILE\.vim\pack\plugins\start\vimscii\plugin.vim"

# Ensure packpath
Add-Content "$env:USERPROFILE\_vimrc" 'set packpath^=~/.vim'
```

---

## Usage

### Open an image directly

```bash
vi image.png
```

Vim automatically:

* Converts it to **ASCII**
* Fits width ≈ 120 columns (height fits window)
* Shows grayscale (no color)
* Replaces the current buffer (no split)

---

### Manual commands (inside Vim)

#### Default render

```vim
:ImgHere
```

#### Advanced control (same as Python CLI)

```vim
:ImgHereArgs --mode braille --width 100
:ImgHereArgs --mode half --color --width 120
:ImgHereArgs --mode ascii --ramp blocks --width 120
:ImgHereArgs --mode braille --natural
```

#### Supported modes

| Mode      | Description                        |
| --------- | ---------------------------------- |
| `ascii`   | Uses ASCII density ramp (default)  |
| `blocks`  | Uses ░▒▓█ shades                   |
| `half`    | Uses half-block vertical pairs     |
| `braille` | 2×4 pixel-per-cell for high detail |

#### Common flags

| Flag                       | Purpose                                       |       |                    |
| -------------------------- | --------------------------------------------- | ----- | ------------------ |
| `--width N` / `--height N` | Resize to fit                                 |       |                    |
| `--natural`                | Render at native resolution                   |       |                    |
| `--color`                  | Enable color                                  |       |                    |
| `--color-mode fg           | bg                                            | auto` | Choose color style |
| `--ramp`                   | Choose character ramp (dense, sparse, blocks) |       |                    |
| `--gamma`                  | Adjust brightness (default: 1.0)              |       |                    |

---

## Configuration

You can override defaults in your `~/.vimrc`:

```vim
let g:vimscii_default_mode = 'ascii'        " 'ascii', 'braille', 'blocks', 'half'
let g:vimscii_default_width = 120
let g:vimscii_default_color = 0             " 0 = grayscale, 1 = color
let g:vimscii_default_ramp = 'dense'
let g:vimscii_default_natural = 0           " 1 = show original scale
```

---

## Examples

**Simple ASCII render:**

```bash
vi image.png
```

**Colored Braille mode (manual):**

```vim
:ImgHereArgs --mode braille --color --width 100
```

**Original scale:**

```vim
:ImgHereArgs --mode ascii --natural
```

**Blocks with shading:**

```vim
:ImgHereArgs --mode blocks --ramp blocks --width 110
```

---

## Command-line example

You can use the converter standalone too:

```bash
python3 ~/.local/bin/img2text.py image.png --mode braille --width 100 --color
```

---

## Notes

* Works completely offline (pure Python).
* No Pillow or external libraries — uses only Python stdlib.
* Make sure your terminal uses a **monospaced font** and **UTF-8 encoding**.
* Bright or dark terminals may require tweaking `--gamma`.

---

## License

```
MIT License

Copyright (c) 2025 Chintan Acharya

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
---

**Author:** [Chintan Acharya](https://github.com/chintan-27)
**Repository:** [github.com/chintan-27/vimscii](https://github.com/chintan-27/vimscii)



