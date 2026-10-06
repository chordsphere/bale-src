"""bale_wizard — the shared presentation layer for bale's interactive wizards.

One place owns how a bale wizard draws itself: the opening title, section
headings, one item per screen with its position in the walk, the state
rows (current / inherited / effective), the prompt that states what Enter
does, on-demand help, notices and reject-with-hint warnings, the
instruction table shown once up front, and the review shown before a
file is written. `bale config init` (bale_config section 3) and the
goal-less `bale pack` wizard (bale_pack's PackWalk) both draw through
it, and both ask their choice screens through `ask_choice` (see
"Extension points").

What this module does NOT own: what an answer *means*. Enter-keeps,
'-'-clears, 'x'-suppresses, the bool spellings, and every reject-with-
hint check stay with the wizard that walks the keys — this layer hands
back the raw answer (or None for EOF/^C) and the caller decides. That
split keeps the "no semantic change" property of a presentation move
checkable in one file.

Import discipline. This is a LEAF module: stdlib only, and it imports
nothing from `bin/` — not `__main__`, not a sibling. Any sibling
(bale_config today, bale_pack next) can therefore import it at module
top by bare name (bin/ is on sys.path; see bale_config's docstring) with
no circular-import hazard, which is why it does not follow the lazy
`from __main__ import ...` idiom the siblings use for bin/bale's helpers.
It also never writes files and never logs: logging stays with the
caller, which knows what was written.

Output rules (the wizard UI contract, pinned by tests/test_wizard_ui.py):
  - Every line fits WIDTH (80) columns. The one exception is a line that
    names an absolute path: those are never broken mid-path, so they may
    run long. All text goes through `wrap`, which enforces both halves.
  - Color and weight are optional decoration, never information. They
    are emitted only when stdout is a TTY, NO_COLOR is absent from the
    environment (any value, including empty, counts as set), and TERM is
    set and not "dumb" — so piped output, captured test output, and
    NO_COLOR runs are plain text byte-for-byte. Escape codes wrap whole
    already-wrapped lines or whole fields, so a substring search over
    the output never straddles one.
  - stdout and input() are looked up at call time, never cached, so
    contextlib.redirect_stdout and a patched builtins.input (the
    in-process test drivers) see every line and every prompt.

Extension points (for the sessions queued behind this one):
  - The choice prompt ("detected default plus a few named alternatives")
    landed with session wizard-defaults as a sibling of `ask_item`:
    `alternatives` draws the numbered lines — each `[n] value` on a line
    of its own, the value exactly as it would be typed, an optional
    aside in parentheses — and `ask_choice` reads the answer, returning
    it raw so the caller maps a number to its value (`pick_number`
    parses one). The one thing ask_choice decides itself is the one
    the checkpoint picker in bale_pack decides: a number outside the
    list is not a pick, so it warns, names the range, and asks again.
    (The picker also keeps one exception config init does not have,
    a cwd file named by the number; `out_of_range_ok` below.)
    Enter, '?', and every other answer mean exactly what they mean at
    `ask_item`. `Alternative` is the row type and `detected_first`
    orders a list so a detected value is [1].
  - Session choice-prompt-convergence moved the pack walk's two
    hand-built choice lists onto the same primitive. An `Alternative`
    may carry a `key`, drawing `[c] code` in place of `[1] code`, and
    `enter`, which marks the row Enter takes; `ask_choice(letters=...)`
    names the letters on its prompt and judges nothing (the session-
    shape question's answer set stays the caller's). For the checkpoint
    picker, whose answers are paths, `ask_choice` takes `show_help=None`
    ('?' is then an answer, not help), the warning's `noun` / `typed`
    words, the `number` parser, and `out_of_range_ok` (a file literally
    named "7" is the path "7"). Every default is config init's behavior,
    so its screens and answers are unchanged.
  - The pack wizard's other prompts map onto `heading`, `ask`,
    `confirm`, and `notice` directly; its y/N exchanges keep their own
    decline defaults by passing `eof=`/`interrupt=` to `confirm`.
"""

from __future__ import annotations

import os
import re
import sys
import textwrap
from typing import Callable, NamedTuple, Optional, Sequence, Union

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

# The terminal width every wizard line is laid out for. 80 is the floor a
# terminal can be assumed to have; nothing measures the real terminal, so a
# wider window simply shows the same layout with room to spare.
WIDTH = 80

# Horizontal rule character for headings. U+2500 is one column wide; the
# wizards already emit UTF-8 (em dashes throughout the descriptions), so it
# adds no new encoding requirement.
RULE = "\u2500"

# The item header's position field is right-aligned to fit "NN/NN"; item
# bodies indent to sit under the key that follows it ("  19/19  key").
POSITION_WIDTH = 5
BODY_INDENT = 2 + POSITION_WIDTH + 2

# The item header line, as a pattern: "<pos>/<total>  <dotted key>". The
# in-process test drivers (tests/test_probe_clipboard_config.py,
# tests/test_layout_and_formats.py, tests/test_wizard_ui.py) find the item
# an input() call belongs to by the most recent line matching this — so it
# is part of the layer's contract, exported rather than re-spelled.
ITEM_HEADER_RE = re.compile(r"^\s*(\d+)/(\d+)  (\S+)")

# A token that names an absolute path: POSIX "/x..." or a Windows drive
# "C:\x" / "C:/x", at the start of the text or after whitespace, an opening
# bracket or quote, or "=" / ":". A lone "/" (as in "a / b") does not count.
_ABS_PATH_RE = re.compile(
    r"""(?:^|[\s(\[{'"=:])(?:/[^\s/]|[A-Za-z]:[\\/])""")

# ANSI SGR codes for the few styles the layer uses.
_SGR = {
    "bold": "1",
    "dim": "2",
    "accent": "36",      # cyan: item keys and headings
    "warn": "33",        # yellow: reject-with-hint lines
    "add": "32",         # green: review additions
    "remove": "31",      # red: review removals
}


def names_absolute_path(text: str) -> bool:
    """True when `text` contains a token naming an absolute path."""
    return bool(_ABS_PATH_RE.search(text))


def color_enabled(stream=None, environ=None) -> bool:
    """Whether styling may be emitted on `stream` (default: sys.stdout).

    Three conditions, all required: the stream is a TTY (never piped
    output), NO_COLOR is absent (https://no-color.org; this layer reads
    any presence as opt-out, empty value included, because the contract
    is "never when NO_COLOR is set"), and TERM names a terminal that is
    not "dumb" (an unset TERM is treated as unknown, hence plain).
    """
    stream = sys.stdout if stream is None else stream
    environ = os.environ if environ is None else environ
    if "NO_COLOR" in environ:
        return False
    term = environ.get("TERM", "")
    if not term or term == "dumb":
        return False
    isatty = getattr(stream, "isatty", None)
    try:
        return bool(isatty and isatty())
    except (OSError, ValueError):
        # A closed or detached stream cannot be a terminal we can style.
        return False


def wrap(text: str, *, indent: int = 0, hang: Optional[int] = None,
         width: int = WIDTH) -> list[str]:
    """Wrap `text` to `width` columns, first line at `indent`, rest at `hang`.

    Long words are broken to keep the width — except when the text names
    an absolute path, where breaking would corrupt the one thing the line
    exists to show; such a line may run past `width` (the contract's one
    exception). Hyphens never break, so flags and dotted keys stay whole.
    Empty text yields one empty line.
    """
    hang = indent if hang is None else hang
    if not text.strip():
        return [""]
    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=" " * indent,
        subsequent_indent=" " * hang,
        break_long_words=not names_absolute_path(text),
        break_on_hyphens=False,
    )
    return wrapper.wrap(text) or [""]


def clip(value: str, limit: int = 40) -> str:
    """Shorten an echoed user value for a one-line notice.

    Used where the wizard quotes back what the operator typed (a rejected
    answer): the value itself is not the information, the reason is, and
    an unbreakable 200-character token would otherwise blow the width.
    """
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "\u2026"


# Rows for `state` and `table`: a value is one string or a list of lines.
Value = Union[str, Sequence[str]]


class Alternative(NamedTuple):
    """One offered alternative on a choice screen.

    `value` is drawn exactly as the operator would type it, so picking
    its number and typing it are the same answer. `note` is a short
    aside ("macOS", "Wayland"); `detected` marks the value detection
    found on this machine or repo, which the aside says and
    `detected_first` puts at [1]. Detection only suggests: nothing in
    this layer acts on a detected value.

    `key` (session choice-prompt-convergence) letters the row: drawn as
    `[key] value` in place of `[n] value`, for a screen whose answers
    are letters (the pack walk's session-shape question) — the key and
    the value are then both answers, and what each means stays the
    caller's. A screen is all lettered or all numbered (`alternatives`
    refuses a mix). `enter` marks the row Enter takes: the aside says
    "Enter", so the screen shows which row a bare Enter picks.
    """
    value: str
    note: str = ""
    detected: bool = False
    key: str = ""
    enter: bool = False

    def aside(self) -> str:
        """The parenthesized text after the value ("" for none): the
        note, then "detected", then "Enter", comma-separated."""
        parts = [self.note] if self.note else []
        if self.detected:
            parts.append("detected")
        if self.enter:
            parts.append("Enter")
        return ", ".join(parts)

    def tag(self, number: int) -> str:
        """What the row's brackets hold: its letter, else its number."""
        return self.key or str(number)


def detected_first(alternatives: Sequence[Alternative]) -> list[Alternative]:
    """`alternatives` with the detected ones first, order otherwise kept.

    The caller numbers the returned list, so the detected value's number
    is 1 — the one keystroke that takes it.
    """
    alts = list(alternatives)
    return ([a for a in alts if a.detected]
            + [a for a in alts if not a.detected])


def pick_range(count: int) -> str:
    """How a prompt names the numbers on offer: "1" or "1-<count>"."""
    return "1" if count == 1 else f"1-{count}"


def pick_letters(letters: Sequence[str]) -> str:
    """How a prompt names the letters on offer: "c/d/t/m/x/r"."""
    return "/".join(letters)


def pick_number(text: str) -> Optional[int]:
    """The number `text` spells (ASCII digits only), else None.

    Only plain ASCII digits count: "²" or "٣" are values, not picks, and
    a sign or a decimal point makes the text a value too. Whether the
    number is in range is the caller's question (ask_choice re-asks on
    an out-of-range one before the caller ever sees it).
    """
    text = text.strip()
    if text and text.isascii() and text.isdigit():
        return int(text)
    return None


class WizardUI:
    """The drawing surface. Stateless apart from the color decision.

    `color` forces styling on or off (tests); None defers to
    `color_enabled()` at each call, so a redirect mid-run is honored.
    """

    def __init__(self, *, color: Optional[bool] = None) -> None:
        self._color = color

    # -- low-level output ----------------------------------------------

    def _styled(self, text: str, *styles: str) -> str:
        enabled = color_enabled() if self._color is None else self._color
        codes = [_SGR[s] for s in styles if s in _SGR]
        if not enabled or not codes or not text:
            return text
        return f"\033[{';'.join(codes)}m{text}\033[0m"

    def _write(self, line: str) -> None:
        print(line, file=sys.stdout)

    def blank(self) -> None:
        """One empty line — the separator between screens."""
        self._write("")

    def emit(self, text: str = "", *, indent: int = 0,
             hang: Optional[int] = None, style: Sequence[str] = ()) -> None:
        """Write `text` wrapped to the width, each line styled whole."""
        for line in wrap(text, indent=indent, hang=hang):
            self._write(self._styled(line, *style) if line.strip() else line)

    def _rule_line(self, lead: str, *, indent: int = 0) -> str:
        """`lead` followed by a rule out to the width (at least 3 chars);
        a bare rule from `indent` to the width when `lead` is empty."""
        if not lead:
            return " " * indent + RULE * (WIDTH - indent)
        pad = WIDTH - indent - len(lead) - 1
        return " " * indent + f"{lead} {RULE * max(3, pad)}"

    # -- structural elements -------------------------------------------

    def title(self, title: str, rows: Sequence[tuple[str, str]] = (),
              intro: str = "") -> None:
        """The wizard's opening: a bold title, labelled rows, an intro."""
        self.blank()
        self._write(self._styled(title, "bold"))
        self._write(RULE * min(WIDTH, max(len(title), 3)))
        if rows:
            self.table(rows, indent=2)
        if intro:
            self.emit(intro, indent=2)

    def heading(self, title: str, note: str = "") -> None:
        """A section heading: blank line, then a ruled title line.

        `note` rides on the same line when it fits, else on the next.
        """
        self.blank()
        lead = f"{RULE * 2} {title}"
        if note and len(lead) + 2 + len(note) + 4 <= WIDTH:
            line = self._rule_line(f"{lead}  {note}")
            self._write(self._styled(line, "accent"))
            return
        self._write(self._styled(self._rule_line(lead), "accent"))
        if note:
            self.emit(note, indent=3, style=("dim",))

    def item(self, position: int, total: int, key: str,
             kind: str = "") -> None:
        """One item's header: position, dotted key, and its answer kind.

        The line always matches ITEM_HEADER_RE. The kind is right-aligned
        when it fits beside the key and dropped onto its own line when not.
        """
        pos = f"{position}/{total}".rjust(POSITION_WIDTH)
        head = f"  {pos}  {key}"
        if kind and len(head) + 2 + len(kind) <= WIDTH:
            gap = WIDTH - len(head) - len(kind)
            self._write(self._styled(head, "bold", "accent")
                        + " " * gap + self._styled(kind, "dim"))
            return
        self._write(self._styled(head, "bold", "accent"))
        if kind:
            self.emit(kind, indent=BODY_INDENT, style=("dim",))

    def summary(self, text: Union[str, Sequence[str]]) -> None:
        """The item's one- or two-line default description.

        A sequence is explicit lines, each wrapped on its own — for a
        summary whose second sentence must start a line (a phrase a reader
        should meet whole, never split across a wrap).
        """
        for line in ([text] if isinstance(text, str) else text):
            self.emit(line, indent=BODY_INDENT)

    def table(self, rows: Sequence[tuple[str, Value]], *, indent: int,
              aside: Sequence[str] = ()) -> None:
        """Labelled rows: label column padded, value wrapped under itself.

        A list value prints one entry per line. `aside[i]`, when present
        and non-empty, follows row i's last line in parentheses (or on its
        own line when it would not fit).
        """
        if not rows:
            return
        label_w = max(len(label) for label, _ in rows)
        hang = indent + label_w + 2
        for i, (label, value) in enumerate(rows):
            lines = [value] if isinstance(value, str) else list(value) or [""]
            note = aside[i] if i < len(aside) else ""
            for j, entry in enumerate(lines):
                # The first entry rides beside the label; later entries of
                # a list start in the value column themselves (padding
                # whitespace would not survive textwrap).
                text, at = ((f"{label.ljust(label_w)}  {entry}", indent)
                            if j == 0 else (entry, hang))
                if j == len(lines) - 1 and note:
                    joined = f"{text}  ({note})"
                    if at + len(joined) <= WIDTH:
                        self._row(joined, at, hang)
                        continue
                    self._row(text, at, hang)
                    self.emit(f"({note})", indent=hang, hang=hang + 1,
                              style=("dim",))
                    continue
                self._row(text, at, hang)

    def _row(self, text: str, at: int, hang: int) -> None:
        """One table row. A row naming an absolute path is written whole
        on one line — label and path together, past the width if need be
        (the contract's exception) — rather than leaving the label
        stranded above a path wrapped onto a line of its own."""
        if names_absolute_path(text):
            self._write(" " * at + text)
            return
        self.emit(text, indent=at, hang=hang)

    def state(self, rows: Sequence[tuple[str, Value]],
              aside: Sequence[str] = ()) -> None:
        """The item's state rows (current / inherited / effective)."""
        self.table(rows, indent=BODY_INDENT, aside=aside)

    def alternatives(self, alternatives: Sequence[Alternative], *,
                     indent: int = BODY_INDENT,
                     label: str = "alternatives") -> None:
        """The numbered alternatives, one `[n] value  (aside)` per line.

        Numbering follows the sequence as given (use `detected_first`
        before calling, and map numbers against that same list). The
        value is never broken: it is what the operator would type. A
        line naming an absolute path may run past the width (the
        contract's exception); otherwise an aside that does not fit
        moves to the next line, under the value. An empty sequence
        draws nothing, label included, so a screen with nothing to offer
        looks exactly as it did before alternatives existed.

        Lettered rows (every alternative carries a `key`) draw as
        `[key] value  (aside)` instead, in the same layout. A mix of
        lettered and numbered rows, or a letter used twice, is refused:
        the prompt could not say what is on offer.
        """
        if not alternatives:
            return
        keys = [alt.key for alt in alternatives]
        if any(keys) and not all(keys):
            raise ValueError("alternatives are all lettered or all numbered")
        if any(keys) and len(set(keys)) != len(keys):
            raise ValueError("alternatives letter a row twice")
        if label:
            self.emit(label, indent=indent, style=("dim",))
        for n, alt in enumerate(alternatives, start=1):
            self._alternative(n, alt, indent)

    def _alternative(self, n: int, alt: Alternative, indent: int) -> None:
        tag = alt.tag(n)
        lead = f"[{tag}] {alt.value}"
        hang = indent + len(f"[{tag}] ")
        aside = alt.aside()
        if aside and indent + len(lead) + 2 + len(aside) + 2 <= WIDTH:
            self._write(" " * indent + lead + "  "
                        + self._styled(f"({aside})", "dim"))
            return
        if names_absolute_path(lead) or indent + len(lead) <= WIDTH:
            self._write(" " * indent + lead)
        else:
            self.emit(lead, indent=indent, hang=hang)
        if aside:
            self.emit(f"({aside})", indent=hang, hang=hang + 1,
                      style=("dim",))

    def notice(self, text: str, *, indent: int = BODY_INDENT) -> None:
        """An informational line (what happened, what was skipped)."""
        self.emit(text, indent=indent)

    def warn(self, text: str, *, indent: int = BODY_INDENT) -> None:
        """A reject-with-hint line: the answer was not taken, and why."""
        self.emit(f"! {text}", indent=indent, hang=indent + 2,
                  style=("warn",))

    def help(self, key: str, paragraphs: Sequence[str],
             answers: str = "") -> None:
        """An item's full description, shown on demand ('?')."""
        self._write(self._styled(
            self._rule_line(f"{RULE * 2} {key}", indent=BODY_INDENT),
            "dim"))
        for para in paragraphs:
            self.emit(para, indent=BODY_INDENT)
        if answers:
            self.emit(answers, indent=BODY_INDENT, hang=BODY_INDENT + 2,
                      style=("dim",))
        self._write(self._styled(
            self._rule_line("", indent=BODY_INDENT), "dim"))

    def review(self, title: str, *, target: str, verdict: str,
               changes: Sequence[tuple[str, str]] = (), note: str = "") -> None:
        """The pre-write review: what will change versus the file on disk.

        `changes` rows are (marker, text) with marker "+" (added), "~"
        (changed) or "-" (removed). `verdict` is the one-line headline
        ("no changes", "3 changes", ...). Nothing is written here.
        """
        self.heading(title)
        self.emit(target, indent=2)
        self.emit(verdict, indent=2, style=("bold",))
        style_for = {"+": ("add",), "-": ("remove",), "~": ("accent",)}
        for marker, text in changes:
            self.emit(f"{marker} {text}", indent=4, hang=6,
                      style=style_for.get(marker, ()))
        if note:
            self.emit(note, indent=2, style=("dim",))

    # -- input -----------------------------------------------------------

    def ask(self, prompt: str, *, indent: int = BODY_INDENT) -> Optional[str]:
        """One input() line, stripped; None on EOF or ^C.

        The prompt is emitted unstyled (readline measures it) and kept on
        one line; callers keep prompt text short enough to fit.
        """
        try:
            raw = input(" " * indent + prompt)
        except (EOFError, KeyboardInterrupt):
            # Finish the interrupted prompt line so the next output starts
            # clean — the same newline the wizards always printed here.
            self._write("")
            return None
        return raw.strip()

    def ask_item(self, enter_action: str, *,
                 show_help: Callable[[], None]) -> Optional[str]:
        """The item prompt: states the Enter action; '?' shows help.

        Returns the stripped answer ("" for Enter) or None for EOF/^C.
        A bare '?' is consumed here — it prints the item's full help via
        `show_help` and asks again — so callers never see it as a value.
        """
        while True:
            answer = self.ask(f"{enter_action} \u00b7 ? help > ")
            if answer != "?":
                return answer
            show_help()

    def ask_choice(self, enter_action: str, *, count: int = 0,
                   show_help: Optional[Callable[[], None]],
                   separator: Optional[str] = None,
                   letters: Sequence[str] = (),
                   noun: str = "alternative",
                   typed: str = "a value",
                   number: Callable[[str], Optional[int]] = pick_number,
                   out_of_range_ok: Optional[Callable[[str], bool]] = None,
                   ) -> Optional[str]:
        """The item prompt on a screen of numbered or lettered alternatives.

        `ask_item`'s contract plus picks: the prompt states the Enter
        action and what is on offer, a bare '?' shows help and asks
        again, and the answer comes back raw \u2014 "" for Enter, None for
        EOF/^C, a pick as typed \u2014 for the caller to map.

        Numbered (`count` >= 1): a number outside 1..count is not a pick
        (the pack wizard's checkpoint picker rule): a warning names the
        range and the prompt asks again, so the caller only ever sees
        in-range numbers. With a `separator` (":" for a list key) each
        entry is judged on its own, so "1:2" picks two and "1:9"
        re-asks. `bale config init` uses exactly this, with the
        defaults below.

        Lettered (`letters`, the rows' keys in screen order; session
        choice-prompt-convergence): the prompt names the letters, and
        nothing is judged here \u2014 a letter, a spelled-out value, and any
        other text all come back raw, because only the caller knows its
        answer set (the session-shape question lowercases, takes
        "contract-doc" for "t", and warns on anything else). Exactly one
        of `count` and `letters` is given.

        The options the pack's checkpoint picker needs, each defaulting
        to config init's behavior:

        - `show_help` None: '?' is an ordinary answer, returned raw, and
          the prompt offers no '? help' (a prompt whose answers are
          paths, where '?' is a path).
        - `noun` / `typed`: the warning's words \u2014 "no {noun} 7; pick
          1-2, type {typed}, or press Enter."
        - `number`: what reads an entry as a number (None when it is
          not one); default pick_number, plain ASCII digits.
        - `out_of_range_ok`: an out-of-range number this accepts comes
          back raw instead of re-asking (the picker takes a file
          literally named "7" in cwd as the path "7").
        """
        if count and letters:
            raise ValueError("ask_choice offers numbers or letters, not both")
        if count < 1 and not letters:
            raise ValueError("ask_choice needs at least one alternative")
        if letters:
            picks = pick_letters(letters)
            offer = f"{picks} picks"
        else:
            picks = pick_range(count)
            offer = "1 picks it" if count == 1 else f"{picks} picks"
        tail = " \u00b7 ? help > " if show_help is not None else " > "
        while True:
            answer = self.ask(f"{enter_action} \u00b7 {offer}{tail}")
            if answer is None:
                return None
            if answer == "?" and show_help is not None:
                show_help()
                continue
            if letters:
                return answer
            entries = answer.split(separator) if separator else [answer]
            stray = [n for n, e in ((number(e), e) for e in entries)
                     if n is not None and not 1 <= n <= count
                     and not (out_of_range_ok and out_of_range_ok(e))]
            if stray:
                self.warn(f"no {noun} {stray[0]}; pick {picks}, type "
                          f"{typed}, or press Enter.")
                continue
            return answer

    def confirm(self, question: str, *, default: bool = True,
                eof: bool = True, interrupt: bool = False) -> bool:
        """A yes/no gate. Enter takes `default`; EOF takes `eof`; ^C takes
        `interrupt`. Anything but y/yes/n/no asks again.

        The wizards' write gate is confirm(default=True, eof=True,
        interrupt=False): Enter writes (so an Enter-through re-run lands
        the file exactly as it always did), a closed stdin writes (the
        pre-review behavior for scripted runs), and ^C at the gate — the
        one deliberate "stop" a user can type there — declines.
        """
        suffix = "[Y/n]" if default else "[y/N]"
        while True:
            try:
                raw = input(f"  {question} {suffix} ")
            except EOFError:
                self._write("")
                return eof
            except KeyboardInterrupt:
                self._write("")
                return interrupt
            answer = raw.strip().lower()
            if answer == "":
                return default
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            self.warn(f"'{clip(raw.strip(), 20)}' is not an answer here; "
                      f"type y or n (Enter means "
                      f"{'yes' if default else 'no'}).", indent=2)


class Walk:
    """A keyed walk: position in the walk and section headings, derived.

    `order` is the walk's dotted keys ("apply.search_paths") in prompt
    order; an item's position is its index there, and the total is the
    order's length — so the "n/N" a user sees cannot drift from the keys
    the wizard actually walks. A section heading is drawn whenever an
    item's section (the text before the first dot) differs from the
    previous item's; `sections` maps a section name to the note shown on
    its heading.
    """

    def __init__(self, ui: WizardUI, order: Sequence[str],
                 sections: Optional[dict[str, str]] = None) -> None:
        if len(set(order)) != len(order):
            raise ValueError("walk order lists a key twice")
        self.ui = ui
        self.order = tuple(order)
        self.sections = dict(sections or {})
        self._section: Optional[str] = None
        self.visited: list[str] = []

    def begin(self, key: str, *, kind: str,
              summary: Union[str, Sequence[str]]) -> None:
        """Open `key`'s screen: heading if the section changed, a blank
        separator, the item header, and the short summary."""
        if key not in self.order:
            raise ValueError(f"{key!r} is not in this walk's order")
        section = key.split(".", 1)[0]
        if section != self._section:
            self._section = section
            self.ui.heading(f"[{section}]", self.sections.get(section, ""))
        self.ui.blank()
        self.ui.item(self.order.index(key) + 1, len(self.order), key, kind)
        if summary:
            self.ui.summary(summary)
        self.visited.append(key)
