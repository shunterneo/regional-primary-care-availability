"""Versioned, review-only observations of public source content.

The complete meaningful text is hashed before previews are shortened. This is
change detection, not rendered-page verification or evidence of clinic intake.
It is deliberately separate from the fail-closed publication adapter.
"""
from __future__ import annotations
import hashlib
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

REVIEW_VERSION = 'review-context-v2'


def normalize_text(raw):
    raw = re.sub(r'\s+', ' ', raw).strip()
    # The register labels this clock as retrieval time. Do not strip other dates.
    return re.sub(
        r'(AS OF THE DATE AND TIME NOTED BELOW)\s+\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M',
        r'\1 [retrieval time]', raw, flags=re.I)


def document_context(content, final_url, format='html'):
    """Return full bounded-fetch context and a versioned digest, never a claim.

    Hidden/style-dependent text can still occur in HTML. Callers must label this
    raw source review, not visible-page or intake verification. Forms and their
    fields are excluded; this monitor does not collect patient submissions.
    """
    links = []
    media = []
    visibility = []
    base_url = final_url
    if format == 'pdf':
        text = normalize_text(content)
    elif format == 'html':
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.title.get_text(' ', strip=True) if soup.title else ''
        dates = [str(m.get('content', '')) for m in soup.select(
            'meta[property="article:published_time"],meta[property="article:modified_time"],'
            'meta[name="date"],meta[name="last-modified"]')]
        base = soup.find('base', href=True)
        if base:
            base_url = urljoin(final_url, base.get('href', ''))
        # Keep headers, footers and navigation: real intake banners sometimes
        # live there. A noisier review lead is safer than silently missing one.
        for node in soup(['script', 'style', 'noscript', 'template', 'svg', 'head',
                          'form', 'input', 'textarea', 'select']):
            node.decompose()
        # A public registration target can change without its label changing.
        # Only hashes are persisted for targets; do not copy URL parameters into
        # review previews. Relative targets are bound to the fetched final URL.
        links = sorted(set(urljoin(base_url, a.get('href', ''))
                           for a in soup.select('a[href]')))
        alt_text = [str(img.get('alt', '')) for img in soup.find_all('img')]
        media = [[node.name, {key: str(node.get(key)) for key in
                  ('src', 'srcset', 'poster', 'data-src', 'data-srcset') if node.has_attr(key)}]
                 for node in soup.find_all(['img', 'source', 'picture', 'video', 'audio', 'iframe', 'object', 'embed'])]
        # These are change signals, not computed-visibility decisions. Attribute
        # changes may alter which of several contradictory messages is visible.
        visibility = [[node.name, {key: node.get(key) for key in
                       ('hidden', 'aria-hidden', 'style', 'class', 'open') if node.has_attr(key)}]
                      for node in soup.find_all(True)]
        text = normalize_text(' '.join([title, *dates, soup.get_text(' ', strip=True), *alt_text]))
    else:
        raise ValueError('Unsupported observation format')
    digest_input = {'version': REVIEW_VERSION, 'format': format,
                    'final_url': final_url, 'base_url': base_url, 'text': text,
                    'link_targets': links, 'media_targets': media, 'visibility_hints': visibility}
    digest = hashlib.sha256(json.dumps(digest_input, sort_keys=True,
                            ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return {'version': REVIEW_VERSION, 'hash': digest, 'text': text,
            'text_length': len(text), 'link_count': len(links),
            'scope': 'raw public source change only; no intake verification'}
