"""Certificate chain and ticket/TMD templates for CIA generation.

This module contains the binary data templates used for CIA file generation.
These are base64-encoded, zlib-compressed templates that are decompressed
at runtime and cached for performance.

TODO: This is technical debt. These should be moved to:
- dsconv/crypto/certchain_provider.py for certificate chains (Task 8.2)
- dsconv/data/templates/ for ticket/TMD templates
- Ideally, use programmatic builders instead of hardcoded templates
"""

import base64
import zlib

# Retail CIA certificate chain (base64-encoded, zlib-compressed)
certchain_retail = b"""
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
JWFnDuv/P7kyh1k="""

# Ticket (blank titlekey and title ID), TMD signature with blank header
# (blank title ID) and blank content info records (base64-encoded, zlib-compressed)
ticket_tmd = b"""
eJxjYGRgYRgFZIOg/PwSXWdHAwgw1o0IhjKTaW83I+2toJMlBAAjgwiQXAPEIlA2CGgwQFzXAsbM
EMH/BMBAOB8vGM1/FAH0/OccAGUmEacfR/J2AAAmBS75"""

# Cache for decompressed templates (performance optimization)
_ticket_tmd_cache: bytes | None = None


def get_ticket_tmd_template() -> bytes:
    """Get decompressed ticket/TMD template.

    Returns the ticket/TMD template, decompressing and caching it on first access.

    Returns:
        Decompressed ticket/TMD template bytes
    """
    global _ticket_tmd_cache
    if _ticket_tmd_cache is None:
        _ticket_tmd_cache = zlib.decompress(base64.b64decode(ticket_tmd))
    return _ticket_tmd_cache
