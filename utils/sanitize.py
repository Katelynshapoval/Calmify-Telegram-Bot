import re
import html


def sanitize_all(text: str) -> str:
    """
    Completely sanitize model output:
    - Removes format headers (html, ```html)
    - Removes ALL HTML
    - Removes Markdown formatting
    - Normalizes newlines
    - Returns plain text safe for Telegram
    """

    if not text:
        return ""

    text = text.strip()

    # ---- 1. Remove format labels and code fences FIRST ----

    # Remove leading "html", "HTML:", etc.
    text = re.sub(r"^(html|HTML|Html)\s*:?\s*", "", text)

    # Remove fenced code blocks ``` or ```html
    text = re.sub(r"^```(?:html)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # ---- 2. Decode HTML entities (&nbsp;, &amp;, etc.) ----
    text = html.unescape(text)

    # ---- 3. Remove DOCTYPE and all HTML tags ----
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    # ---- 4. Remove Markdown formatting ----
    text = re.sub(r"[*_`~]", "", text)

    # ---- 5. Normalize newlines and whitespace ----

    # Convert escaped newlines to real ones
    text = text.replace("\\n", "\n")

    # Normalize excessive spacing
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()
