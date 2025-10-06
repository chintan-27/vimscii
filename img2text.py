#!/usr/bin/env python3
"""
img2text.py — View images as ASCII/Braille/Blocks directly in Vim or terminal.
Pure Python (stdlib only) — supports PNG, BMP, PPM/PGM (non-interlaced).
"""

import sys, os, struct, zlib, shutil, argparse

RESET = "\x1b[0m"
def ansi_fg(r,g,b): return f"\x1b[38;2;{r};{g};{b}m"
def luma(r,g,b): return int(0.299*r + 0.587*g + 0.114*b + 0.5)

# ---------------- Character ramps ----------------
RAMPS = {
    "ascii": " .'`^,:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "dense": " .,:;-+=*#%@",
    "sparse": " .'`:^*+x%#",
    "blocks": " ░▒▓█",
    "dots": " .:!*oO8@",
    "bars": " ▁▂▃▄▅▆▇█",
    "thin": " `'.,:^-=+*#%@",
}

# ---------------- RGBA image object ----------------
class RGBAImage:
    def __init__(self,w,h,buf): self.size=(w,h); self.buf=buf
    def resize_nn(self,tw,th):
        w,h=self.size; out=bytearray(tw*th*4)
        for ty in range(th):
            sy=min(h-1,int(ty*h/th)); row_off=sy*w*4
            for tx in range(tw):
                sx=min(w-1,int(tx*w/tw))*4
                i=(ty*tw+tx)*4
                out[i:i+4]=self.buf[row_off+sx:row_off+sx+4]
        return RGBAImage(tw,th,bytes(out))

# ---------------- PNG loader (non-interlaced) ----------------
PNG_SIG=b"\x89PNG\r\n\x1a\n"
def _paeth(a,b,c):
    p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
    return a if pa<=pb and pa<=pc else (b if pb<=pc else c)
def _png_chunks(b):
    i=8; n=len(b)
    while i+8<=n:
        L=struct.unpack(">I",b[i:i+4])[0]; t=b[i+4:i+8]
        s=i+8; e=s+L; payload=b[s:e]; i=e+4
        yield t,payload
def _unfilter(raw,w,h,bpp):
    stride=w*bpp; out=bytearray(h*stride); prev=bytearray(stride)
    mv=memoryview(raw); off=0; oi=0
    for _ in range(h):
        f=mv[off]; off+=1; s=mv[off:off+stride]; off+=stride
        d=memoryview(out)[oi:oi+stride]
        if f==0: d[:]=s
        elif f==1:
            for x in range(stride):
                left=d[x-bpp] if x>=bpp else 0
                d[x]=(s[x]+left)&255
        elif f==2:
            for x in range(stride): d[x]=(s[x]+prev[x])&255
        elif f==3:
            for x in range(stride):
                left=d[x-bpp] if x>=bpp else 0
                up=prev[x]; d[x]=(s[x]+((left+up)>>1))&255
        elif f==4:
            for x in range(stride):
                left=d[x-bpp] if x>=bpp else 0
                up=prev[x]; ul=prev[x-bpp] if x>=bpp else 0
                d[x]=(s[x]+_paeth(left,up,ul))&255
        prev[:]=d; oi+=stride
    return bytes(out)
def _unpack_bits(row_bytes,w,bits_per_sample,spp):
    out=[]; total=w*spp; acc=0; nbits=0; it=iter(row_bytes)
    while len(out)<total:
        if nbits<bits_per_sample:
            try: acc=(acc<<8)|next(it)
            except StopIteration: break
            nbits+=8; continue
        shift=nbits-bits_per_sample
        val=(acc>>shift)&((1<<bits_per_sample)-1)
        nbits-=bits_per_sample
        if bits_per_sample==1: val=0 if val==0 else 255
        elif bits_per_sample==2: val=val*85
        elif bits_per_sample==4: val=val*17
        out.append(val)
    while len(out)<total: out.append(0)
    return bytes(out)

def load_png(path):
    b=open(path,"rb").read()
    if not b.startswith(PNG_SIG): return None
    ihdr=None; plte=None; trns=None; idat=bytearray()
    for t,p in _png_chunks(b):
        if t==b'IHDR': ihdr=struct.unpack(">IIBBBBB",p)
        elif t==b'PLTE': plte=p
        elif t==b'tRNS': trns=p
        elif t==b'IDAT': idat.extend(p)
        elif t==b'IEND': break
    if not ihdr: raise ValueError("PNG missing IHDR")
    w,h,bit_depth,color_type,comp,flt,interlace=ihdr
    if comp or flt or interlace: raise ValueError("Only non-interlaced PNG supported")
    if color_type==0: spp,mode=1,"G"
    elif color_type==2: spp,mode=3,"RGB"
    elif color_type==3: spp,mode=1,"P"
    elif color_type==4: spp,mode=2,"GA"
    elif color_type==6: spp,mode=4,"RGBA"
    else: raise ValueError("Unsupported color type")
    bpp=max(1,(spp*bit_depth+7)//8)
    raw=zlib.decompress(bytes(idat))
    scan=_unfilter(raw,w,h,bpp)
    out=bytearray(w*h*4)
    if mode=="P":
        if not plte: raise ValueError("Palette missing")
        pal=[tuple(plte[i:i+3]) for i in range(0,len(plte),3)]
        alpha=list(trns) if trns else []
        row_stride=(w*bit_depth+7)//8; off=0; di=0
        for _ in range(h):
            rb=scan[off:off+row_stride]; off+=row_stride
            smp=_unpack_bits(rb,w,bit_depth,1) if bit_depth<8 else rb
            for x in range(w):
                idx=smp[x]
                r,g,b=pal[idx] if idx<len(pal) else (0,0,0)
                a=alpha[idx] if idx<len(alpha) else 255
                out[di:di+4]=bytes((r,g,b,a)); di+=4
    else:
        di=0; off=0
        for _ in range(h):
            row_len=w*spp*(1 if bit_depth==8 else 2)
            row=scan[off:off+row_len]; off+=row_len
            si=0
            for _ in range(w):
                if bit_depth==16:
                    vals=[row[si+2*j] for j in range(spp)]; si+=2*spp
                else:
                    vals=list(row[si:si+spp]); si+=spp
                if mode=="G": g=vals[0]; out[di:di+4]=bytes((g,g,g,255)); di+=4
                elif mode=="GA": g,a=vals; out[di:di+4]=bytes((g,g,g,a)); di+=4
                elif mode=="RGB": r,g,b=vals; out[di:di+4]=bytes((r,g,b,255)); di+=4
                else: r,g,b,a=vals; out[di:di+4]=bytes((r,g,b,a)); di+=4
    return RGBAImage(w,h,bytes(out))

# ---------------- BMP / PPM loaders ----------------
def load_bmp(p):
    d=open(p,"rb").read()
    if len(d)<54 or d[:2]!=b"BM": return None
    w,h,_,bpp,comp=struct.unpack("<iiHHI",d[18:18+16])
    if comp!=0 or bpp not in (24,32): raise ValueError("Only uncompressed 24/32-bit BMP")
    off=struct.unpack("<I",d[10:14])[0]; row=((bpp*w+31)//32)*4; px=d[off:]
    out=bytearray(abs(h)*w*4); height=abs(h)
    for rowi in range(height):
        sy=rowi if h<0 else height-1-rowi; ro=sy*row; di=rowi*w*4
        for x in range(w):
            if bpp==24:
                b,g,r=px[ro+x*3:ro+x*3+3]; a=255
            else:
                b,g,r,a=px[ro+x*4:ro+x*4+4]
            out[di:di+4]=bytes((r,g,b,a)); di+=4
    return RGBAImage(w,height,bytes(out))
def load_ppm_pgm(p):
    f=open(p,"rb"); m=f.read(2)
    if m not in (b"P5",b"P6"): return None
    def tok():
        t=b""; c=f.read(1)
        while c and c in b" \t\r\n": c=f.read(1)
        while c==b"#":
            while c and c not in b"\r\n": c=f.read(1)
            while c and c in b" \t\r\n": c=f.read(1)
        while c and c not in b" \t\r\n": t+=c; c=f.read(1)
        return t
    w=int(tok()); h=int(tok()); mv=int(tok())
    if mv!=255: raise ValueError("Only maxval 255")
    count=w*h*(1 if m==b"P5" else 3); data=f.read(count)
    out=bytearray(w*h*4); si=0; di=0
    if m==b"P5":
        for _ in range(w*h):
            g=data[si]; si+=1; out[di:di+4]=bytes((g,g,g,255)); di+=4
    else:
        for _ in range(w*h):
            r,g,b=data[si:si+3]; si+=3; out[di:di+4]=bytes((r,g,b,255)); di+=4
    return RGBAImage(w,h,bytes(out))

def load_image(p):
    for f in (load_png,load_bmp,load_ppm_pgm):
        try:
            im=f(p)
            if im: return im
        except Exception: pass
    raise SystemExit("Unsupported or unreadable image.")

# ---------------- Scaling helper ----------------
def scale_to_cells(img,mode,width_cells=None,height_cells=None,char_aspect=None):
    w,h=img.size
    if mode=="braille": pw,ph,asp=2,4,0.5
    elif mode=="half": pw,ph,asp=1,2,0.5
    else: pw,ph=1,1; asp=0.5 if char_aspect is None else float(char_aspect)
    if width_cells is None and height_cells is None:
        width_cells=max(1,shutil.get_terminal_size((80,24)).columns-2)
    if height_cells is None:
        height_cells=max(1,int((h/float(w))*width_cells*asp))
    elif width_cells is None:
        width_cells=max(1,int((w/float(h))*height_cells/asp))
    tw,th=width_cells*pw,height_cells*ph
    return img.resize_nn(tw,th),width_cells,height_cells

# ---------------- Renderers ----------------
def render_blocks(img,width=None,height=None,ramp="ascii",gamma=1.0,color=False):
    ramp_str=RAMPS.get(ramp,ramp)
    img,cw,ch=scale_to_cells(img,"blocks",width,height)
    w,h=img.size; px=img.buf; out=[]
    for cy in range(ch):
        y0=int(cy*(h/ch)); y1=max(y0+1,int((cy+1)*(h/ch)))
        row=[]
        for cx in range(cw):
            x0=int(cx*(w/cw)); x1=max(x0+1,int((cx+1)*(w/cw)))
            rs=gs=bs=c=0
            for y in range(y0,y1):
                off=y*w*4
                for x in range(x0,x1):
                    i=off+x*4; r,g,b,a=px[i:i+4]
                    if a!=255:
                        ar=a/255.0; r=int(ar*r+(1-ar)*255+0.5)
                        g=int(ar*g+(1-ar)*255+0.5); b=int(ar*b+(1-ar)*255+0.5)
                    rs+=r; gs+=g; bs+=b; c+=1
            r,g,b=rs//c,gs//c,bs//c; Y=luma(r,g,b)
            if gamma!=1.0: Y=int((Y/255.0)**gamma*255+0.5)
            glyph=ramp_str[int((Y/255.0)*(len(ramp_str)-1)+.5)]
            row.append((ansi_fg(r,g,b)+glyph+RESET) if color else glyph)
        out.append("".join(row))
    return "\n".join(out)

def render_half(img,width=None,height=None,gamma=1.0,color=False):
    img,cw,ch=scale_to_cells(img,"half",width,height)
    w,h=img.size; px=img.buf; out=[]
    for y in range(0,h,2):
        row=[]
        for x in range(w):
            i1=(y*w+x)*4; r1,g1,b1,a1=px[i1:i1+4]
            if a1!=255:
                ar=a1/255.0; r1=int(ar*r1+(1-ar)*255+0.5)
                g1=int(ar*g1+(1-ar)*255+0.5); b1=int(ar*b1+(1-ar)*255+0.5)
            if y+1<h:
                i2=((y+1)*w+x)*4; r2,g2,b2,a2=px[i2:i2+4]
                if a2!=255:
                    ar=a2/255.0; r2=int(ar*r2+(1-ar)*255+0.5)
                    g2=int(ar*g2+(1-ar)*255+0.5); b2=int(ar*b2+(1-ar)*255+0.5)
            else: r2=g2=b2=255
            Y1,Y2=luma(r1,g1,b1),luma(r2,g2,b2)
            if gamma!=1.0:
                Y1=int((Y1/255.0)**gamma*255+0.5); Y2=int((Y2/255.0)**gamma*255+0.5)
            if Y1<128 and Y2<128: ch='█'; cr=((r1+r2)//2,(g1+g2)//2,(b1+b2)//2)
            elif Y1<128: ch='▀'; cr=(r1,g1,b1)
            elif Y2<128: ch='▄'; cr=(r2,g2,b2)
            else: ch=' '; cr=(255,255,255)
            row.append((ansi_fg(*cr)+ch+RESET) if color else ch)
        out.append("".join(row))
    return "\n".join(out)

BRAILLE_BASE=0x2800
BRAILLE_BITS=[(0,0,1),(0,1,2),(0,2,3),(0,3,7),(1,0,4),(1,1,5),(1,2,6),(1,3,8)]
def render_braille(img,width=None,height=None,gamma=1.0,color=False):
    img,cw,ch=scale_to_cells(img,"braille",width,height)
    w,h=img.size; px=img.buf; out=[]
    for cy in range(0,h,4):
        row=[]
        for cx in range(0,w,2):
            bits=0; rs=gs=bs=c=0
            for dx,dy,bit in BRAILLE_BITS:
                sx,sy=cx+dx,cy+dy
                if sx>=w or sy>=h: continue
                i=(sy*w+sx)*4; r,g,b,a=px[i:i+4]
                if a!=255:
                    ar=a/255.0; r=int(ar*r+(1-ar)*255+0.5)
                    g=int(ar*g+(1-ar)*255+0.5); b=int(ar*b+(1-ar)*255+0.5)
                Y=luma(r,g,b)
                if gamma!=1.0: Y=int((Y/255.0)**gamma*255+0.5)
                if Y<128: bits|=(1<<(bit-1))
                rs+=r; gs+=g; bs+=b; c+=1
            ch=chr(BRAILLE_BASE+bits)
            if color and c: r,g,b=rs//c,gs//c,bs//c; row.append(ansi_fg(r,g,b)+ch+RESET)
            else: row.append(ch)
        out.append("".join(row))
    return "\n".join(out)

# ---------------- CLI ----------------
def parse_args(argv):
    ap=argparse.ArgumentParser(description="Pure Python image→text")
    ap.add_argument("image")
    ap.add_argument("--mode",choices=["braille","half","ascii","blocks"],default="braille")
    ap.add_argument("--ramp",default="dense")
    ap.add_argument("--width",type=int,default=None)
    ap.add_argument("--height",type=int,default=None)
    ap.add_argument("--gamma",type=float,default=1.0)
    ap.add_argument("--color",action="store_true")
    ap.add_argument("--char-aspect",type=float,default=None)
    return ap.parse_args(argv)

def main():
    a=parse_args(sys.argv[1:])
    img=load_image(a.image)
    if a.mode=="braille": out=render_braille(img,a.width,a.height,a.gamma,a.color)
    elif a.mode=="half": out=render_half(img,a.width,a.height,a.gamma,a.color)
    else: out=render_blocks(img,a.width,a.height,a.ramp,a.gamma,a.color)
    print(out)

if __name__=="__main__": main()

