#!/usr/bin/env python3
"""Turn Arch's stock gtk4 PKGBUILD into the Nemesis gtk4-live-css one.

    derive-pkgbuild.py arch/PKGBUILD > PKGBUILD

Why: GTK 4 loads $XDG_CONFIG_HOME/gtk-4.0/gtk.css once, when the display opens,
so a theme switch only reaches GTK 4 apps started afterwards. The patch carried
next to this script makes GTK watch that file and reload the provider it already
created, so open windows restyle like the bar and the terminal do.

Everything Arch does stays as it is -- version, build options, dependency and
makedepend lists. What changes:

  * one package, `gtk4-live-css`, which provides and conflicts with `gtk4`.
    Arch's `package_gtk4()` becomes `package()`; the demos, docs and
    gtk-update-icon-cache splits are dropped (we do not replace them).
  * gtk4-user-css-live-reload.patch is added to `source` (with its blake2
    checksum), and applied in `prepare()`.

Every edit asserts that it matched exactly once, so a reshaped upstream PKGBUILD
fails the build loudly instead of producing an unpatched or half-renamed package.

Arch's PKGBUILD lives at
https://gitlab.archlinux.org/archlinux/packaging/packages/gtk4/-/raw/main/PKGBUILD
"""

import hashlib
import re
import sys
from pathlib import Path

PATCH = "gtk4-user-css-live-reload.patch"
here = Path(__file__).resolve().parent

src = sys.argv[1] if len(sys.argv) > 1 else None
if not src:
    sys.exit(__doc__.strip().splitlines()[2].strip())
text = Path(src).read_text()


def once(old: str, new: str) -> None:
    """Replace exactly one occurrence, or die."""
    global text
    count = text.count(old)
    if count != 1:
        sys.exit(f"derive-pkgbuild: expected 1 match, found {count} for: {old!r}")
    text = text.replace(old, new, 1)


# 1. One package instead of pkgbase + four split packages.
m = re.search(r"^pkgbase=gtk4\npkgname=\(\n(?:  [^\n]*\n)+?\)\n", text, re.M)
if not m:
    sys.exit("derive-pkgbuild: pkgbase=gtk4 / pkgname=( ... ) block not found")
text = text[: m.start()] + "pkgname=gtk4-live-css\n" + text[m.end():]

once(
    'pkgdesc="GObject-based multi-platform GUI toolkit"',
    'pkgdesc="GObject-based multi-platform GUI toolkit, with the user gtk.css reloaded live"',
)

# 2. Ship the patch as a second source, with its checksum.
m = re.search(r"^source=\(\n(?:  [^\n]*\n)+?\)\n", text, re.M)
if not m:
    sys.exit("derive-pkgbuild: source=( ... ) block not found")
text = text[: m.end() - 2] + f"  {PATCH}\n)\n" + text[m.end():]

digest = hashlib.blake2b((here / PATCH).read_bytes(), digest_size=64).hexdigest()
m = re.search(r"^b2sums=\((?:'[0-9a-f]+'\s*)+\)", text, re.M)
if not m:
    sys.exit("derive-pkgbuild: b2sums=( ... ) block not found")
text = text[: m.end() - 1] + f"\n        '{digest}')" + text[m.end():]

# 3. Apply it.
once("prepare() {\n  cd gtk\n", f"prepare() {{\n  cd gtk\n  patch -Np1 -i ../{PATCH}\n")

# 4. package_gtk4() becomes the single package, standing in for gtk4.
once("package_gtk4() {\n", "package() {\n")
once(
    "  provides=(libgtk-4.so)\n",
    '  provides=("gtk4=$epoch:$pkgver-$pkgrel" libgtk-4.so)\n'
    "  conflicts=(gtk4)\n",
)

# 5. Do not build the API documentation or man pages: they belong to the
#    gtk4-docs split package, which we drop, and gi-docgen over the whole GTK
#    API is by far the slowest part of the build (it dominated a 40-minute run).
once("-D documentation=true", "-D documentation=false")
once("-D man-pages=true", "-D man-pages=false")

# 6. Drop the splits we do not replace.
for name in ("gtk4-demos", "gtk4-docs", "gtk-update-icon-cache"):
    m = re.search(rf"^package_{re.escape(name)}\(\) \{{\n.*?^\}}\n\n?", text, re.M | re.S)
    if not m:
        sys.exit(f"derive-pkgbuild: package_{name}() not found")
    text = text[: m.start()] + text[m.end():]

sys.stdout.write(text)
