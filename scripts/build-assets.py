#!/usr/bin/env python3
"""Build the profile README SVGs in ../assets.

Every glyph is converted to an outline (JetBrains Mono, SIL OFL 1.1), so the
cards render identically on every OS and browser. Edit the CONTENT section and
re-run:  python3 scripts/build-assets.py

Requires: fontTools, JetBrains Mono installed (FONT_DIR below).
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

FONT_DIR = Path("/usr/share/fonts/TTF")
OUT = Path(__file__).resolve().parent.parent / "assets"

FONTS = {
    "r": "JetBrainsMono-Regular.ttf",
    "m": "JetBrainsMono-Medium.ttf",
    "b": "JetBrainsMono-Bold.ttf",
    "x": "JetBrainsMono-ExtraBold.ttf",
    "i": "JetBrainsMono-Italic.ttf",
}

PALETTES = {
    "dark": dict(
        card="#0d1117", panel="#151b23", border="#30363d", rule="#21262d",
        fg="#e6edf3", op="#b1bac4", muted="#9198a1", dim="#656c76", faint="#464e59",
        accent="#f0b44c", soft="rgba(240,180,76,0.10)",
    ),
    "light": dict(
        card="#ffffff", panel="#f6f8fa", border="#d1d9e0", rule="#e6eaef",
        fg="#1f2328", op="#424a53", muted="#59636e", dim="#818b98", faint="#aab3bd",
        accent="#9a6700", soft="rgba(154,103,0,0.09)",
    ),
}

# --------------------------------------------------------------------------
# glyph machinery

class Font:
    def __init__(self, key, file):
        self.key = key
        self.tt = TTFont(FONT_DIR / file)
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.upm = self.tt["head"].unitsPerEm
        self.adv = self.tt["hmtx"]["A"][0]  # monospaced

    def path(self, ch):
        pen = SVGPathPen(self.gs, ntos=lambda v: str(round(v)))
        self.gs[self.cmap[ord(ch)]].draw(pen)
        return pen.getCommands()


FONT = {k: Font(k, f) for k, f in FONTS.items()}


def n(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


class Doc:
    def __init__(self, w, h, pal, title, desc):
        self.w, self.h, self.p = w, h, pal
        self.title, self.desc = title, desc
        self.defs = {}
        self.body = []

    def cw(self, size):
        return size * 0.6

    def text(self, x, y, s, size, font="r", cls="fg"):
        f = FONT[font]
        k = size / f.upm
        uses = []
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            gid = f"{font}{ord(ch):x}"
            if gid not in self.defs:
                self.defs[gid] = f.path(ch)
            uses.append(f'<use href="#{gid}" x="{i * f.adv}"/>')
        return (f'<g class="{cls}" transform="translate({n(x)} {n(y)}) '
                f'scale({n(k)} {n(-k)})">{"".join(uses)}</g>')

    def spans(self, x, y, parts, size, font="r"):
        out, cx = [], x
        for part in parts:
            s, cls = part[0], part[1]
            fnt = part[2] if len(part) > 2 else font
            if s.strip():
                out.append(self.text(cx, y, s, size, fnt, cls))
            cx += len(s) * self.cw(size)
        return "".join(out)

    def add(self, *items):
        self.body.extend(items)

    def render(self, css):
        p = self.p
        defs = "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.defs.items())
        base = f"""
.fg{{fill:{p['fg']}}} .op{{fill:{p['op']}}} .mu{{fill:{p['muted']}}}
.dim{{fill:{p['dim']}}} .fa{{fill:{p['faint']}}} .ac{{fill:{p['accent']}}}
.in{{animation:in .7s cubic-bezier(.2,.7,.2,1) both}}
@keyframes in{{from{{opacity:0}}to{{opacity:1}}}}
.blink{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{0%,55%{{opacity:1}}56%,100%{{opacity:0}}}}
.live{{animation:live 2.6s ease-in-out infinite}}
@keyframes live{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">'
                f'<title id="t">{self.title}</title><desc id="d">{self.desc}</desc>'
                f'<style>{base}{css}</style><defs>{defs}</defs>{"".join(self.body)}</svg>\n')

    # shared chrome ---------------------------------------------------------
    def card(self, left, right):
        p, w, h = self.p, self.w, self.h
        self.add(
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" '
            f'fill="{p["card"]}" stroke="{p["border"]}"/>',
            f'<path d="M1 40.5H{w - 1}" stroke="{p["rule"]}"/>',
            f'<circle class="live" cx="28" cy="20.5" r="4" fill="{p["accent"]}"/>',
            self.text(44, 25, left, 13, "m", "mu"),
            self.text(w - 24 - len(right) * self.cw(13), 25, right, 13, "r", "dim"),
        )


# --------------------------------------------------------------------------
# CONTENT

# (address, raw bytes, mnemonic, operand parts, comment parts)
LISTING = [
    (0x401000, "55",                   "push", [("rbp", "op")], []),
    (0x401001, "48 89 e5",             "mov",  [("rbp,rsp", "op")], []),
    (0x401004, "48 8d 3d f5 0f 00 00", "lea",  [("rdi,[rip+", "op"), ("0xff5", "ac"), ("]", "op")],
                                               [("# ", "dim"), ("0x402000", "dim"), (" <bio>", "ac")]),
    (0x40100b, "e8 f0 00 00 00",       "call", [("0x401100", "ac"), (" <reverse_engineer>", "ac")], []),
    (0x401010, "31 c0",                "xor",  [("eax,eax", "op")], []),
    (0x401012, "c9",                   "leave", [], []),
    (0x401013, "c3",                   "ret",  [], []),
]

# register file *before* each instruction executes (what gdb shows at `=>`)
REGS = ["rax", "rdi", "rsp", "rbp", "rip"]
_S = dict(rax=0x1c, rdi=0x1, rsp=0x7ffd3a2c9e48, rbp=0x7ffd3a2c9e70)
STATES = []
for addr, *_ in LISTING:
    STATES.append(dict(_S, rip=addr))
    if addr == 0x401000: _S["rsp"] -= 8                       # push rbp
    if addr == 0x401001: _S["rbp"] = _S["rsp"]                # mov rbp,rsp
    if addr == 0x401004: _S["rdi"] = 0x402000                 # lea rdi,[rip+0xff5]
    if addr == 0x40100b: _S["rax"] = 0x2a                     # call -> returns 42
    if addr == 0x401010: _S["rax"] = 0                        # xor eax,eax
    if addr == 0x401012: _S["rsp"], _S["rbp"] = _S["rbp"] + 8, 0x7ffd3a2c9e70  # leave

# sanity: rip-relative and call displacements match the encoded bytes
assert 0x401004 + 7 + 0xff5 == 0x402000
assert 0x40100b + 5 + 0xf0 == 0x401100

SECTIONS = [  # name, type, flags, contents
    (".text",        "PROGBITS", "AX", "C · C++ · Rust"),
    (".text.asm",    "PROGBITS", "AX", "x86-64 assembly"),
    (".debug",       "PROGBITS", "",   "reverse engineering · disassembly · debugging"),
    (".note.os",     "NOTE",     "A",  "Linux · x64 internals"),
    (".data.engine", "PROGBITS", "WA", "Unreal Engine"),
    (".rodata",      "PROGBITS", "A",  "Python · tooling"),
    (".comment",     "PROGBITS", "MS", "philosophy · theology · rigorous thinking"),
]

STEP = 1.25   # seconds per instruction
DELAY = 1.2   # before stepping starts


# --------------------------------------------------------------------------
# header: gdb session

def header(pal):
    W, H = 1000, 566
    d = Doc(W, H, pal, "tmpleos",
            "A gdb session stepping through a function named tmpleos: "
            "self-taught systems programmer; reverse engineering, x64 internals, C, C++, Rust.")
    d.card("gdb ./tmpleos", "0x00")
    p, X = pal, 48
    T = STEP * len(LISTING)

    # identity block
    d.add('<g class="in">',
          d.spans(X, 86, [("7f ", "fa"), ("45 4c 46", "ac"), (" 02 01 01 00", "fa"),
                          ("   ELF64 · x86-64", "dim")], 13),
          '</g><g class="in" style="animation-delay:.08s">',
          d.text(X - 3, 164, "tmpleos", 78, "x", "fg"),
          '</g><g class="in" style="animation-delay:.16s">',
          d.spans(X, 204, [("0x402000", "dim"), (" <bio>", "ac"), (": ", "dim"), ('"', "dim"),
                           ("self-taught systems programmer", "fg"), ('"', "dim")], 15),
          '</g><g class="in" style="animation-delay:.24s">')
    px = X
    for tag in ["reverse engineering", "x64 internals", "C / C++ / Rust"]:
        tw = len(tag) * d.cw(12.5) + 24
        d.add(f'<rect x="{n(px + .5)}" y="224.5" width="{n(tw)}" height="25" rx="12.5" '
              f'fill="none" stroke="{p["border"]}"/>',
              d.text(px + 12, 241.5, tag, 12.5, "m", "mu"))
        px += tw + 10
    d.add("</g>")

    # register panel
    RX, RY, RW = 652, 62, 300
    d.add('<g class="in" style="animation-delay:.3s">',
          f'<rect x="{RX + .5}" y="{RY + .5}" width="{RW}" height="186" rx="10" '
          f'fill="{p["panel"]}" stroke="{p["rule"]}"/>',
          d.spans(RX + 18, RY + 27, [("info registers", "dim")], 12.5, "m"))
    for r, reg in enumerate(REGS):
        y = RY + 60 + r * 27
        d.add(d.text(RX + 18, y, reg, 15, "m", "dim"))
        for i, st in enumerate(STATES):
            changed = i > 0 and STATES[i - 1][reg] != st[reg]
            cls = "ac" if (changed or reg == "rip") else "fg"
            d.add(f'<g class="v{" v0" if i == 0 else ""}" '
                  f'style="animation-delay:{n(DELAY + i * STEP)}s">',
                  d.text(RX + 66, y, f"0x{st[reg]:016x}", 15, "r", cls), "</g>")
    d.add("</g>")

    # disassembly
    d.add(f'<path d="M24 276.5H{W - 24}" stroke="{p["rule"]}"/>')
    d.add('<g class="in" style="animation-delay:.36s">',
          d.spans(X, 312, [("(gdb) ", "dim"), ("disassemble /r tmpleos", "fg")], 15), "</g>")
    Y0, DY = 350, 25
    cw = d.cw(15)
    # stepping highlight (behind text)
    d.add('<g class="pc">',
          f'<rect x="30" y="{Y0 - 17}" width="{W - 60}" height="24" rx="5" fill="{p["soft"]}"/>',
          f'<rect x="30" y="{Y0 - 17}" width="3" height="24" rx="1.5" fill="{p["accent"]}"/>',
          d.text(X, Y0, "=>", 15, "b", "ac"), "</g>")
    for r, (addr, raw, mn, ops, cm) in enumerate(LISTING):
        y = Y0 + r * DY
        off = f"<+{addr - LISTING[0][0]}>:"
        parts = [(f"0x{addr:x}", "dim"), (" " + off.ljust(9), "fa"), (raw.ljust(23), "fa")]
        d.add(f'<g class="in" style="animation-delay:{n(.42 + r * .05)}s">',
              d.spans(X + 3 * cw, y, parts, 15),
              d.text(X + 43 * cw, y, mn, 15, "m", "fg"),
              d.spans(X + 50 * cw, y, ops, 15) if ops else "",
              d.spans(X + 70 * cw, y, cm, 15) if cm else "",
              "</g>")
    yp = Y0 + len(LISTING) * DY + 22
    d.add('<g class="in" style="animation-delay:.8s">',
          d.spans(X, yp, [("(gdb) ", "dim"), ("si", "fg")], 15),
          f'<rect class="blink" x="{n(X + 9 * cw)}" y="{yp - 14}" width="{n(cw)}" height="18" '
          f'fill="{p["accent"]}"/>', "</g>")

    # keyframes: hold on each row, glide quickly to the next
    k, frames = len(LISTING), []
    for i in range(k):
        a, b = 100 * i / k, 100 * (i + 1) / k - 1.6
        frames.append(f"{n(a)}%,{n(b)}%{{transform:translateY({i * DY}px)}}")
    frames.append(f"100%{{transform:translateY(0)}}")
    css = (f".pc{{animation:pc {n(T)}s cubic-bezier(.6,0,.2,1) {n(DELAY)}s infinite}}"
           f"@keyframes pc{{{''.join(frames)}}}"
           f".v{{opacity:0;animation:show {n(T)}s linear infinite}} .v0{{opacity:1}}"
           f"@keyframes show{{0%,{n(100 / k - .01)}%{{opacity:1}}{n(100 / k)}%,100%{{opacity:0}}}}")
    return d.render(css)


# --------------------------------------------------------------------------
# toolchain: readelf -S

def toolchain(pal):
    W, H = 1000, 436
    d = Doc(W, H, pal, "toolchain",
            "Section headers of tmpleos: C, C++, Rust; x86-64 assembly; reverse engineering, "
            "disassembly, debugging; Linux and x64 internals; Unreal Engine; Python; "
            "philosophy, theology, rigorous thinking.")
    d.card("readelf -S ./tmpleos", "0x01")
    X, cw = 48, d.cw(15)
    d.add('<g class="in">',
          d.spans(X, 82, [("$ ", "dim"), ("readelf -S --wide ./tmpleos", "fg")], 15),
          d.text(X, 116, "Section Headers:", 15, "r", "mu"),
          d.spans(X + 2 * cw, 148, [("[Nr] ", "dim"), ("Name".ljust(15), "dim"),
                                    ("Type".ljust(11), "dim"), ("Flg  ", "dim"), ("Contents", "dim")], 15),
          "</g>")
    for i, (name, typ, flg, what) in enumerate(SECTIONS):
        y = 180 + i * 26
        d.add(f'<g class="in" style="animation-delay:{n(.1 + i * .07)}s">',
              d.spans(X + 2 * cw, y, [(f"[{i + 1:>2}] ", "fa"), (name.ljust(15), "fg", "m"),
                                      (typ.ljust(11), "mu"), (flg.ljust(5), "ac", "m")], 15))
        cx = X + 38 * cw
        for j, item in enumerate(what.split(" · ")):
            if j:
                d.add(d.text(cx, y, " · ", 15, "r", "fa"))
                cx += 3 * cw
            d.add(d.text(cx, y, item, 15, "r", "op"))
            cx += len(item) * cw
        d.add("</g>")
    yk = 180 + len(SECTIONS) * 26 + 16
    d.add('<g class="in" style="animation-delay:.7s">',
          d.text(X, yk, "Key to Flags:", 13, "r", "dim"),
          d.spans(X + 2 * d.cw(13), yk + 22,
                  [("W", "ac"), (" (write), ", "dim"), ("A", "ac"), (" (alloc), ", "dim"),
                   ("X", "ac"), (" (execute), ", "dim"), ("M", "ac"), (" (merge), ", "dim"),
                   ("S", "ac"), (" (strings)", "dim")], 13),
          "</g>")
    return d.render("")


# --------------------------------------------------------------------------
# footer

def footer(pal):
    W, H = 1000, 84
    d = Doc(W, H, pal, "ret", "ret ; fides quaerens intellectum")
    p = pal
    parts = [("c3", "ac", "m"), ("  ret", "fg", "m"), ("    ; ", "fa"),
             ("fides quaerens intellectum", "mu", "i")]
    tw = sum(len(s[0]) for s in parts) * d.cw(15)
    x0 = (W - tw) / 2
    d.add('<g class="in">',
          f'<path d="M48 42.5H{n(x0 - 28)}M{n(x0 + tw + 28)} 42.5H{W - 48}" stroke="{p["border"]}"/>',
          d.spans(x0, 47.5, parts, 15), "</g>")
    return d.render("")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in [("header", header), ("toolchain", toolchain), ("footer", footer)]:
        for theme, pal in PALETTES.items():
            f = OUT / f"{name}-{theme}.svg"
            f.write_text(fn(pal))
            print(f"{f.relative_to(OUT.parent)}  {f.stat().st_size / 1024:.1f} KiB")
