from pathlib import Path
import shutil

path = Path("app/strategy/reversal_family.py")
backup = Path("app/strategy/reversal_family.py.bak")

# Create a backup first
shutil.copy2(path, backup)

text = path.read_text(encoding="utf-8")


def indent_block(text, start_marker, end_marker):
    start = text.index(start_marker)
    end = text.index(end_marker, start)

    block = text[start:end]

    lines = block.splitlines(keepends=True)
    fixed = []

    for line in lines:
        if line.strip():
            fixed.append("    " + line)
        else:
            fixed.append(line)

    return text[:start] + "".join(fixed) + text[end:]


# ---------------------------------------------------------
# Move the broken sequence methods into the class
# ---------------------------------------------------------

text = indent_block(
    text,
    "def _evaluate_bullish_sequence(",
    "def _detect_bullish_repeated_tests("
)

text = indent_block(
    text,
    "def _detect_bullish_repeated_tests(",
    "def _detect_bearish_repeated_tests("
)

text = indent_block(
    text,
    "def _detect_bearish_repeated_tests(",
    "def _evaluate_bearish_sequence("
)

# Stop BEFORE the existing class-level BOS methods.
text = indent_block(
    text,
    "def _evaluate_bearish_sequence(",
    "    # ---------------------------------------------------------\n    # BOS"
)


# ---------------------------------------------------------
# Remove the duplicate top-level _prices_close method
# ---------------------------------------------------------

start = text.index("def _prices_close(self, first, second, tolerance_pct=None):")

# Find the next top-level retest method.
end = text.index(
    "def _find_bullish_retest(",
    start
)

text = text[:start] + text[end:]


# ---------------------------------------------------------
# Move retest helpers into the class
# ---------------------------------------------------------

text = indent_block(
    text,
    "def _find_bullish_retest(",
    "def _find_bearish_retest("
)

text = indent_block(
    text,
    "def _find_bearish_retest(",
    "    # ---------------------------------------------------------\n    # Pullback / retest"
)


path.write_text(text, encoding="utf-8")

print("Repair completed.")
print(f"Backup created: {backup}")
