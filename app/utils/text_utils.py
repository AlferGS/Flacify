# app/utils/text_utils.py

_SUSPICIOUS_CHARS = frozenset('ÃÂÄÖÜÝÞßåëïîáæÿøñýþðçêôùûüÿ')

def sanitize_metadata_text(text: str) -> str | None:
    """
    Проверяет текст на наличие mojibake (кракозябр).
    
    Возвращает:
    - Исправленный текст, если удалось раскодировать
    - Исходный текст, если он читаемый
    - None, если текст содержит подозрительные символы
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