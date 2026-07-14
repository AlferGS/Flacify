# app/utils/text_utils.py

_SUSPICIOUS_CHARS = frozenset('ÃÂÄÖÜÝÞßåëïîáæÿøñýþðçêôùûüÿ')

def sanitize_metadata_text(text: str) -> str | None:
    """
    Checks text for mojibake (or gibberish).

    Returns:
    - The corrected text, if decoded successfully
    - The original text, if readable
    - None, if the text contains suspicious characters
    """
    if not text or not text.strip():
        return None
    
    if _SUSPICIOUS_CHARS.intersection(text):
        return None
    
    try:
        fixed = text.encode('latin-1').decode('utf-8')
        if fixed != text:
            return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    return text