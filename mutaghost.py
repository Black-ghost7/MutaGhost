#!/usr/bin/env python3
"""MutaGhost - keyword-based password mutation generator.

Derived from Psudohash by Panagiotis Chartas (t3l3machus):
https://github.com/t3l3machus/psudohash
Used and modified under the MIT License. See LICENSE and NOTICE.md.

Builds a wordlist of realistic password variants from one or more
keywords: leetspeak substitutions, upper/lower case variants, numbering,
years, and common paddings before/after the word.

For education and authorized security testing only.
"""

import argparse
import itertools
import os
import shutil
import sys
import time

VERSION = "1.0.1"
AUTHOR = "Black-ghost7"
REPO = "https://github.com/Black-ghost7/MutaGhost"

COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

GRADIENT = (117, 123, 86, 85, 49, 48)   # light blue -> mint/spring green, top to bottom

LOGO = [
    " ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗",
    "██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝",
    "██║  ███╗███████║██║   ██║███████╗   ██║   ",
    "██║   ██║██╔══██║██║   ██║╚════██║   ██║   ",
    "╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ",
    " ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ",
]

TRANSFORMATIONS = [
    {"a": "@"},
    {"b": "8"},
    {"e": "3"},
    {"g": ["9", "6"]},
    {"i": ["1", "!"]},
    {"o": "0"},
    {"s": ["$", "5"]},
    {"t": "7"},
]
TRANS_KEYS = [key for item in TRANSFORMATIONS for key in item]

COMMON_PADDINGS = [
    "!", "@", "#", "$", "%", "^", "&", "*", ",", ".", "?", "-",
    "123", "234", "345", "456", "567", "678", "789", "890",
    "!@", "@#", "#$", "$%", "%^", "^&", "&*", "*(", "()",
    "!@#", "@#$", "#$%", "$%^", "%^&", "^&*", "&*(", "*()", ")_+",
    "1!1", "2@2", "3#3", "4$4", "5%5", "6^6", "7&7", "8*8", "9(9", "0)0",
    "@2@", "#3#", "$4$", "%5%", "^6^", "&7&", "*8*", "(9(",
    "!@!", "@#@", "!@#$%", "1234", "12345", "123456", "123!@#",
    "!!!", "@@@", "###", "$$$", "%%%", "^^^", "&&&", "***", "(((", ")))",
    "---", "+++",
    "11", "12", "13", "22", "1122",
] + [str(y) for y in range(1945, 2031) if y not in (2007,)] + [
    "@" + str(y) for y in range(1945, 2031)
] + [
    "$" + str(y) for y in range(1945, 2031)
]


class MutaGhostError(Exception):
    pass


def paint(code, text):
    return "\033[%sm%s\033[0m" % (code, text) if COLOR else text


def cyan(text):
    return paint("96", text)


def green(text):
    return paint("92", text)


def yellow(text):
    return paint("93", text)


def red(text):
    return paint("91", text)


def gray(text):
    return paint("90", text)


def ok(msg):
    print("%s %s" % (green("[+]"), msg))


def info(msg):
    print("%s %s" % (cyan("[*]"), msg))


def warn(msg):
    print("%s %s" % (yellow("[!]"), msg))


def fail(msg):
    print("%s %s" % (red("[-]"), msg))


def c256(n, text):
    return "\033[38;5;%dm%s\033[0m" % (n, text) if COLOR else text


def show_banner():
    if shutil.get_terminal_size((80, 24)).columns >= 48:
        print(paint("1;97", "   M  U  T  A"))
        for i, row in enumerate(LOGO):
            print(c256(GRADIENT[i], row))
    else:                                    # narrow screens (phones)
        print(paint("1;97", "  MUTAGHOST"))
    print(gray("  v%s  |  derived from Psudohash by t3l3machus  |  %s" % (VERSION, AUTHOR)))
    print(gray("  " + REPO))
    print()


# --------------------------------------------------------------- mutation

def unique(seq):
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_years(spec):
    years = []
    spec = spec.strip()
    if "," in spec:
        for part in spec.split(","):
            part = part.strip()
            if not (part.isdecimal() and 1000 <= int(part) <= 3200):
                raise MutaGhostError("illegal year '%s' (range 1000-3200)" % part)
            years.append(part)
    elif "-" in spec:
        start, _, end = spec.partition("-")
        if not (start.isdecimal() and end.isdecimal() and int(start) < int(end)
                and 1000 <= int(start) and int(end) <= 3200):
            raise MutaGhostError("illegal year range '%s' (1000-3200, start < end)" % spec)
        years = [str(y) for y in range(int(start), int(end) + 1)]
    elif spec.isdecimal() and 1000 <= int(spec) <= 3200:
        years = [spec]
    else:
        raise MutaGhostError("illegal year value '%s' (range 1000-3200)" % spec)
    return years


def case_mutations(word):
    return list(map("".join, itertools.product(*zip(word.upper(), word.lower()))))


def leet_positions(word):
    """Return the list of character indices in `word` that have a substitution."""
    return [i for i, ch in enumerate(word) if ch in TRANS_KEYS]


def leet_mutations(base_words, word, positions):
    """Expand `base_words` with every leetspeak substitution at `positions`."""
    cage = list(base_words)
    for pos in positions:
        char = word[pos].lower()
        trans = TRANSFORMATIONS[TRANS_KEYS.index(char)][char]
        options = trans if isinstance(trans, list) else [trans]
        grown = []
        for current in cage:
            for opt in options:
                chars = list(current)
                chars[pos] = opt
                grown.append("".join(chars))
        cage.extend(grown)
    return cage


def numbering_variants(words, level, limit):
    out = []
    for word in words:
        for digits in range(1, level + 1):
            for k in range(1, limit + 1):
                tag = str(k).zfill(digits)
                out.append(word + tag)
                out.append(word + "_" + tag)
    return out


def year_variants(words, years):
    out = []
    for word in words:
        for year in years:
            out.append(word + year)
            out.append(word + "_" + year)
            out.append(word + year[2:])
    return out


def padding_variants(words, paddings, before):
    out = []
    for word in words:
        for pad in paddings:
            if before:
                out.append(pad + word)
                if pad[-1:] != "_":
                    out.append(pad + "_" + word)
            else:
                out.append(word + pad)
                if pad[:1] != "_":
                    out.append(word + "_" + pad)
    return out


SAFETY_LIMIT = 5_000_000
SAFETY_SECONDS = 8


def collect(word, args, on_progress):
    """Compute every unique mutation of `word` in memory and return it as a list.

    Raises MutaGhostError if the caller aborts after a safety-limit warning.
    """
    word = word.strip()
    words = unique(case_mutations(word.lower()))
    positions = leet_positions(word.lower())
    if positions:
        words = unique(leet_mutations(words, word.lower(), positions))
    else:
        info("'%s' has no character to substitute; using case variants only" % word)

    stages = [words]
    if args.append_numbering:
        stages.append(numbering_variants(words, args.append_numbering, args.numbering_limit))
    if args.years:
        stages.append(year_variants(words, args.years))
    if args.paddings_after:
        stages.append(padding_variants(words, args.paddings, before=False))
    if args.paddings_before:
        stages.append(padding_variants(words, args.paddings, before=True))

    result = []
    seen = set()
    start = time.time()
    warned = False
    for stage in stages:
        for item in stage:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
            if len(result) % 2000 == 0:
                on_progress(len(result))
                if not warned and (len(result) >= SAFETY_LIMIT
                                   or time.time() - start >= SAFETY_SECONDS):
                    warned = True
                    print()
                    warn("Already at %s unique words for '%s' and still counting." %
                         (format(len(result), ","), word))
                    if not confirm("Keep going? [y/N]: "):
                        raise MutaGhostError("stopped by user during '%s' (partial counts are not written)" % word)
    on_progress(len(result))
    return result


# -------------------------------------------------------------- progress

class Progress:
    """A bar with a known total (used while writing the final file)."""

    def __init__(self, label, total):
        self.label = label
        self.total = max(total, 1)
        self.start = time.time()

    def update(self, count):
        pct = min(100, int(count * 100 / self.total))
        bar = "#" * (pct // 4) + "-" * (25 - pct // 4)
        elapsed = time.time() - self.start
        rate = count / elapsed if elapsed > 0 else 0
        print("\r%s %s [%s] %3d%%  %d words  (%.0f/s)" %
              (cyan("[*]"), self.label, bar, pct, count, rate), end="", flush=True)

    def done(self, count):
        elapsed = time.time() - self.start
        print("\r" + " " * 90, end="\r")
        ok("%s: %d words in %.1fs" % (self.label, count, elapsed))


class LiveCounter:
    """A counter with no known total (used while counting unique mutations)."""

    def __init__(self, label):
        self.label = label
        self.start = time.time()

    def update(self, count):
        elapsed = time.time() - self.start
        rate = count / elapsed if elapsed > 0 else 0
        print("\r%s Counting '%s' mutations... %s so far  (%.0f/s)" %
              (cyan("[*]"), self.label, format(count, ","), rate), end="", flush=True)

    def done(self, count):
        elapsed = time.time() - self.start
        print("\r" + " " * 90, end="\r")
        ok("'%s': %s unique mutations in %.1fs" % (self.label, format(count, ","), elapsed))


# ------------------------------------------------------------------- cli

def read_keywords(args):
    keywords = []
    if args.words:
        keywords += [w.strip() for w in args.words.split(",") if w.strip()]
    if args.wordlist:
        try:
            with open(args.wordlist, encoding="utf-8") as handle:
                for line in handle:
                    for part in line.strip().split(","):
                        part = part.strip()
                        if part:
                            keywords.append(part)
        except OSError as err:
            raise MutaGhostError("cannot read %s: %s" % (args.wordlist, err))
    keywords = unique(keywords)
    if not keywords:
        raise MutaGhostError("no keywords given (use -w or -wl)")
    for word in keywords:
        if word.isdecimal():
            raise MutaGhostError("'%s' is digits only; keywords need at least one letter" % word)
    return keywords


def confirm(prompt):
    try:
        answer = input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer.strip().lower() in ("y", "yes")


def run(args):
    keywords = read_keywords(args)
    paddings = list(args.paddings)
    if args.custom_only:
        if not paddings:
            raise MutaGhostError("--custom-only needs --padding VALUES")
    elif args.paddings_before or args.paddings_after:
        paddings = unique(COMMON_PADDINGS + paddings)
    args.paddings = paddings

    info("Keywords: %s" % ", ".join(keywords))

    # Phase 1: compute every unique mutation in memory, so the count and size
    # shown below are exact, not a guess (unlike Psudohash's pre-run estimate).
    collected = {}
    grand_total = 0
    total_bytes = 0
    for word in keywords:
        counter = LiveCounter(word)
        words = collect(word, args, counter.update)
        counter.done(len(words))
        collected[word] = words
        grand_total += len(words)
        total_bytes += sum(len(w) + 1 for w in words)

    print()
    print("%s This will write exactly %s words (%s) to %s" %
          (yellow("[!]"), green(format(grand_total, ",")),
           human_size(total_bytes), cyan(args.output)))
    if not args.yes and not confirm("Continue? [y/N]: "):
        warn("Aborted, nothing written")
        return 1

    # Phase 2: write the already-computed, already-deduplicated lists to disk.
    open(args.output, "w").close()
    with open(args.output, "a", encoding="utf-8") as handle:
        for word in keywords:
            words = collected[word]
            progress = Progress("Writing '%s'" % word, len(words))
            for i, item in enumerate(words, 1):
                handle.write(item + "\n")
                if i % 2000 == 0:
                    progress.update(i)
            progress.done(len(words))
    ok("Done. %s total words written to %s" % (format(grand_total, ","), args.output))
    return 0


def human_size(num_bytes):
    if num_bytes < 1024:
        return "%d B" % num_bytes
    if num_bytes < 1024 * 1024:
        return "%.1f KB" % (num_bytes / 1024)
    return "%.1f MB" % (num_bytes / (1024 * 1024))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mutaghost",
        description="Keyword-based password mutation generator (derived from Psudohash).",
        epilog="For education and authorized security testing only.",
    )
    parser.add_argument("--version", action="version", version="mutaghost " + VERSION)
    parser.add_argument("-w", "--words", metavar="LIST",
                        help="comma-separated keywords to mutate")
    parser.add_argument("-wl", "--wordlist", metavar="FILE",
                        help="read keywords from a file (one per line, or comma-separated)")
    parser.add_argument("-an", "--append-numbering", type=int, metavar="LEVEL",
                        help="append numbering (digits) after each mutation, e.g. 2 -> 01..50")
    parser.add_argument("-nl", "--numbering-limit", type=int, default=None, metavar="LIMIT",
                        help="max number for -an (default 50)")
    parser.add_argument("-y", "--years", metavar="YEARS",
                        help="years to append: single, comma list, or range (1990-2022)")
    parser.add_argument("-ap", "--padding", dest="padding_values", metavar="VALUES",
                        help="comma-separated custom padding values")
    parser.add_argument("-cpb", "--paddings-before", action="store_true",
                        help="add common paddings before each mutation")
    parser.add_argument("-cpa", "--paddings-after", action="store_true",
                        help="add common paddings after each mutation")
    parser.add_argument("-cpo", "--custom-only", action="store_true",
                        help="use only --padding values, not the built-in list")
    parser.add_argument("-o", "--output", default="mutaghost_output.txt", metavar="FILE",
                        help="output file (default mutaghost_output.txt)")
    parser.add_argument("--yes", action="store_true", dest="yes",
                        help="skip the confirmation prompt")
    parser.add_argument("--no-color", action="store_true", help="disable colors")
    parser.add_argument("--menu", action="store_true", help="force the interactive menu")
    return parser


def finalize_args(args):
    args.years = parse_years(args.years) if args.years else None
    args.paddings = [v.strip() for v in args.padding_values.split(",") if v.strip()] \
        if args.padding_values else []
    if args.numbering_limit is not None and not args.append_numbering:
        raise MutaGhostError("--numbering-limit needs --append-numbering")
    if args.append_numbering is not None and args.append_numbering <= 0:
        raise MutaGhostError("--append-numbering must be >= 1")
    args.numbering_limit = args.numbering_limit or 50
    if args.custom_only and not (args.paddings_before or args.paddings_after):
        raise MutaGhostError("--custom-only needs --paddings-before or --paddings-after")
    return args


# -------------------------------------------------------------- menu ui

def ask(prompt, default=""):
    try:
        value = input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise MutaGhostError("cancelled")
    return value.strip() or default


def menu_build_args():
    parser = build_parser()
    args = parser.parse_args([])

    print(green("  Interactive setup") + gray("  (press Enter to accept the default)"))
    print()
    args.words = ask("  Keywords, comma separated: ")
    while not args.words:
        warn("at least one keyword is required")
        args.words = ask("  Keywords, comma separated: ")

    wl = ask("  Also read keywords from a file (path, or Enter to skip): ")
    args.wordlist = wl or None

    an = ask("  Append numbering after each word? digits, e.g. 2 (Enter to skip): ")
    args.append_numbering = int(an) if an.isdecimal() and int(an) > 0 else None
    if args.append_numbering:
        nl = ask("  Max number for numbering [50]: ", "50")
        args.numbering_limit = int(nl) if nl.isdecimal() else 50

    yr = ask("  Years to append, e.g. 1990-2024 (Enter to skip): ")
    args.years = parse_years(yr) if yr else None

    pa = ask("  Add common paddings AFTER each word? [y/N]: ").lower() in ("y", "yes")
    pb = ask("  Add common paddings BEFORE each word? [y/N]: ").lower() in ("y", "yes")
    args.paddings_after, args.paddings_before = pa, pb
    if pa or pb:
        extra = ask("  Extra custom paddings, comma separated (Enter to skip): ")
        args.paddings = [v.strip() for v in extra.split(",") if v.strip()]
    else:
        args.paddings = []

    out = ask("  Output file [mutaghost_output.txt]: ", "mutaghost_output.txt")
    args.output = out
    args.yes = False
    args.custom_only = False
    return args


def interactive_main():
    show_banner()
    while True:
        try:
            args = menu_build_args()
        except MutaGhostError:
            warn("cancelled")
            return 1
        print()
        try:
            rc = run(args)
        except MutaGhostError as err:
            fail(str(err))
            rc = 1
        print()
        again = ask("Generate another wordlist? [y/N]: ")
        if again.lower() not in ("y", "yes"):
            return rc


def main(argv=None):
    global COLOR
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.no_color:
        COLOR = False

    interactive = args.menu or (argv is None and len(sys.argv) == 1)
    try:
        if interactive:
            return interactive_main()
        show_banner()
        args = finalize_args(args)
        return run(args)
    except MutaGhostError as err:
        fail(str(err))
        return 1
    except KeyboardInterrupt:
        print()
        warn("Interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
