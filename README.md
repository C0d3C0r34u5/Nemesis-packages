# Nemesis packages

The pacman repository for [Nemesis](https://github.com/C0d3C0r34u5/Nemesis)
binaries. The distro source stays private; this repo holds the build recipes
and the published packages.

## Use it

```
[nemesis]
SigLevel = Required DatabaseOptional
Server = https://github.com/C0d3C0r34u5/Nemesis-packages/releases/download/repo
```

Every package is signed with the **Nemesis Packages** key:

```
D22DAB01 600C1374 46DB07A1 ECA6BF2B ECD2A25F
```

Trust it once (a Nemesis install does this for you — the public key ships with
the ISO and is added to the pacman keyring):

```sh
pacman-key --add /path/to/nemesis-packages.asc
pacman-key --lsign-key D22DAB01600C137446DB07A1ECA6BF2BECD2A25F
```

## What is in here

| recipe | package | what it is |
| --- | --- | --- |
| `gtk4-live-css/` | `gtk4-live-css` | Arch's `gtk4` with the user `gtk.css` reloaded live, so open GTK 4 apps follow a theme switch (see its README) |

Each recipe is derived from Arch's packaging at build time, so the packages
track the repos instead of going stale. Builds run in
`.github/workflows/`, are signed when the `GPG_PRIVATE_KEY` secret is present,
and are uploaded to the `repo` release (package + `repo-add` database).

## Adding a recipe

A recipe is `NAME/` containing whatever `derive-pkgbuild.py` (or a plain
`PKGBUILD`) needs, plus a workflow that builds it and uploads the `*.pkg.tar.zst`
to the `repo` release. Keep the package name inside the release tag `repo` so
clients keep one `Server =` line.

## Notes

* The signing key is a dedicated, passphrase-less key used only by CI. Its
  primary copy (and the revocation certificate) is held offline; rotate by
  publishing a new key and a keyring update.
* Nothing here is built from Nemesis's installer sources — these are patches
  and packaging only.
