import re
import unicodedata

def slugify(text: str, max_length: int = 80) -> str:
    """
    Converts a string into a URL-friendly slug.

    Args:
        text (str): The input text to slugify.
        max_length (int): The maximum allowed length of the resulting slug.

    Returns:
        str: The generated URL slug.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    # 1. Unicode Normalization (NFKD) and combining character stripping
    # This step converts characters like é -> e + accent mark, then removes the accent mark.
    normalized_string = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

    # 2. Lowercase conversion
    s = normalized_string.lower()

    # 3. Replace non-alphanumeric runs with a single hyphen
    # We replace anything that isn't a letter, number, or space with nothing first,
    # then handle whitespace/punctuation groups.
    s = re.sub(r'[^\w\s-]', '', s).strip()

    # 4. Replace contiguous runs of whitespace or hyphens/spaces with a single hyphen
    s = re.sub(r'[-\s]+', '-', s)

    # 5. Strip leading/trailing hyphens
    slug = s.strip('-')

    # 6. Truncate and handle potential trailing hyphens from truncation
    if len(slug) > max_length:
        truncated_slug = slug[:max_length]
        # If the truncation happens right before a hyphen, we need to ensure it's clean.
        # We slice up to (and including) the character at max_length - 1.
        if len(slug) > max_length:
            final_slug = slug[:max_length].rstrip('-')
        else:
             final_slug = slug
    else:
        final_slug = slug

    # Ensure it never ends with a hyphen even after truncation/cleanup
    return final_slug.strip('-')


if __name__ == "__main__":
    print("--- Running Slugify Assertions ---")

    # Test 1: Basic text, punctuation, and whitespace handling
    assert slugify("   Hello World! This is a test slug... ", max_length=50) == "hello-world-this-is-a-test-slug"

    # Test 2: Unicode characters (French 'é')
    assert slugify("Café Latte for Paris", max_length=50) == "cafe-latte-for-paris"

    # Test 3: Complex non-Latin script and symbols (Japanese, emojis, etc.)
    # NFKD + ASCII encoding handles most of this by removing the non-ASCII parts.
    assert slugify("日本語 Blog ✨ with $$$ signs.", max_length=50) == "blog-with-signs"

    # Test 4: Leading/Trailing Separators and excessive delimiters
    assert slugify("--A very--long---title---", max_length=100) == "a-very-long-title"

    # Test 5: Max Length Truncation (should cut gracefully without leaving a hyphen)
    long_text = "This is an extremely long string that needs to be truncated because it exceeds eighty characters limit."
    expected_slug = "this-is-an-extremely-long-string-that-needs-" # Cut at max 80, ending in 'e'
    assert slugify(long_text, max_length=21) == "this-is-an-ex"

    # Test 6: Empty or nearly empty input
    assert slugify("") == ""
    assert slugify("  \t\n ", max_length=50) == ""

    # Test 7 (Edge case): Testing a string that is exactly the max length and ends cleanly
    max_text = "a" * 12 + "-" + "b" * 68
    expected_slug_full = "aaaaaaaaaaaa-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert slugify(max_text, max_length=100) == expected_slug_full

    # Test 8 (Edge case): Max length cut precisely at a hyphen boundary
    # The input is "a-b-c". Length 5. We want the output to be 'a-b'.
    assert slugify("a-b-c", max_length=3) == "a" # Because slice gives 'a-b', but then re-strips potentially left over hyphen

    print("\nAll assertions passed successfully!")