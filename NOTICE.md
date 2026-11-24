# Notice of derivation

MutaGhost is a derivative work based on **Psudohash**, created by
Panagiotis Chartas ([@t3l3machus](https://github.com/t3l3machus)):

> https://github.com/t3l3machus/psudohash

Psudohash is licensed under the MIT License. MutaGhost reuses and modifies
its mutation algorithms (character substitution, case variation, numbering,
years and padding) under the terms of that license. See [LICENSE](LICENSE)
for the full text, which covers both the original work and the changes
described below.

## What was kept from Psudohash

- The core idea: generate realistic password variants from one or more
  keywords for authorized password-strength testing.
- The character-substitution table (leetspeak), the case-variation logic,
  the numbering and year-suffix logic, and the concept of common padding
  values placed before/after a word.

## What MutaGhost changes

- Full rewrite of the code structure (functions, naming, CLI).
- A colored interactive menu, in addition to command-line flags.
- A real, live progress indicator while mutations are generated.
- An **exact** word/size count computed before writing to disk (instead of
  an upper-bound estimate), with a safety prompt if a run grows very large.
- Reading keywords from a file (`-wl/--wordlist`), on top of `-w/--words`.
- A desktop icon, application-menu entry, and an installer for several
  Linux distributions and for Termux (Android).

MutaGhost is not affiliated with or endorsed by the Psudohash project.
If you use MutaGhost's output or code in your own work, please keep this
notice and the attribution to the original project.
