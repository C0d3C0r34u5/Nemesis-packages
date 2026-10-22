# gtk4-live-css — GTK 4 with live reloading of the user's `gtk.css`

GTK 4 loads `$XDG_CONFIG_HOME/gtk-4.0/gtk.css` **once**, when the display opens,
and never looks at it again. So a theme switch reaches the bar and the terminal
immediately, but every open GTK 4 app keeps its old colours until it is
restarted (this is why Nemesis's file manager is the GTK 3 Thunar).

This directory carries a patch that makes GTK watch that file and reload the
provider it already created for it. Open windows restyle the moment the file
changes — the same thing GTK 3 does.

## What the patch does

`gtk4-user-css-live-reload.patch` (against `gtk/gtksettings.c`):

* after `settings_init_style()` loads the user provider, `user_css_watch()`
  installs a `GFileMonitor` on the `gtk.css` path — **and** on whatever the path
  resolves to when it is a symlink (`realpath`), so swapping a symlink and
  rewriting the file behind it both count;
* on `CHANGED` / `CHANGES_DONE_HINT` / `CREATED` / `DELETED` / `RENAMED` /
  `MOVED_IN` / `MOVED_OUT` it debounces 150 ms (a theme switch writes several
  files in a row) and then reloads the *same* provider with
  `gtk_css_provider_load_from_path()`, or empties it if the file is gone;
* the style cascade then restyles every open window, exactly as if the app had
  just started.

It is a fork of the user-css provider only, so libadwaita apps get it too. The
idea comes from <https://github.com/saneaspect/gtk4-live-css> (which ships
prebuilt packages from an unsigned, `TrustAll` pacman repo). This copy is
written for Nemesis so the code, the build and the signing are ours.

Verified on the dev host with Nautilus (GTK 4): rewriting `gtk.css` while the
window was open changed its colours live, both in place and across an atomic
`mv` replacement.

## Building

`derive-pkgbuild.py` turns Arch's stock `gtk4` PKGBUILD into ours — same
version, options, depends and makedepends; one package named `gtk4-live-css`
that provides/conflicts with `gtk4`, with the patch added to `source` and
applied in `prepare()`:

```sh
curl -fsSL -o arch.PKGBUILD \
  https://gitlab.archlinux.org/archlinux/packaging/packages/gtk4/-/raw/main/PKGBUILD
python3 derive-pkgbuild.py arch.PKGBUILD > PKGBUILD
cp gtk4-user-css-live-reload.patch .
makepkg -s            # ~10-30 min, pins every core
sudo pacman -U gtk4-live-css-*.pkg.tar.zst
```

Every edit asserts it matched exactly once, so when Arch reshapes the PKGBUILD
(or GTK changes `gtksettings.c` and the patch stops applying) the build fails
loudly instead of producing a package that silently lost the patch.

`../.github/workflows/gtk4-live-css.yml` does the same on a daily schedule and
publishes the package + pacman database to the `gtk4-live-css-repo` release, so
the version tracks Arch. It skips the build when that version is already
published, and signs the package and database when a `GPG_PRIVATE_KEY` secret
is set.

## Trade-offs (read before enabling it)

* This **replaces a core library**. Packages that link `libgtk-4.so` keep
  working (it is the same soname), but Nemesis now owns GTK 4 updates: if the
  patch stops applying, CI fails and GTK stays at the last good build until it
  is fixed. That is the cost of the feature.
* Until the package is signed and the repo has a real `SigLevel`, clients must
  trust it explicitly — do not ship `TrustAll` in a default `pacman.conf`.
* It only matters for apps that actually render through GTK 4. Nothing on a
  stock Nemesis does by default: Thunar and `gnome-disk-utility` are GTK 3, and
  **LibreOffice is not a GTK 4 app either** — it runs its own toolkit (VCL) with
  optional GTK backends, and Arch lists both `gtk3` and `gtk4` as *optional*
  deps (`gtk4: for GTK4 integration (experimental)`). It picks `gtk3` here;
  `SAL_USE_VCLPLUGIN=gtk4 soffice` forces the experimental one, which would then
  follow this patch too. The real beneficiaries are flatpak GTK 4 apps and
  anything GTK 4 added later.

## Licence

The patch modifies GTK (`LGPL-2.1-or-later`) and is distributed under the same
terms. `derive-pkgbuild.py` and this file are part of the Nemesis repo.
