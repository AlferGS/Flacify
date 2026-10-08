#utils/text_utils.py
def _looks_like_mojibake(text: str) -> bool:
    """True if text contains a UTF-8 lead byte (0xC2..0xF4) immediately followed
    by a continuation byte (0x80..0xBF) — the signature of UTF-8 mis-decoded as
    Latin-1/CP1252. Valid accented letters (ö, ü, ñ, å, ß, ...) never match."""
    for i in range(len(text) - 1):
        a = ord(text[i])
        b = ord(text[i + 1])
        if 0xC2 <= a <= 0xF4 and 0x80 <= b <= 0xBF:
            return True
    return False


def sanitize_metadata_text(text: str) -> str | None:
    """
    Normalize possibly-mojibaked metadata text.

    Returns:
    - The repaired text, if Latin-1 -> UTF-8 decoding fixes it
    - The original text, if it is readable (including valid accents)
    - None, if the text is empty or still looks like unrecoverable mojibake
    """
    if not text or not text.strip():
        return None

    try:
        repaired = text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        repaired = text

    if repaired != text and not _looks_like_mojibake(repaired):
        return repaired
    if _looks_like_mojibake(text):
        return None
    return text