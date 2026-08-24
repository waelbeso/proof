from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.utils import timezone
from django.utils.dateparse import parse_datetime

MAX_BYTES = 512_000
TIMEOUT = 6

class UnsafeSourceURL(ValueError):
    pass


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise UnsafeSourceURL('Only public http/https URLs are allowed.')
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeSourceURL('Host could not be resolved.') from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_multicast, ip.is_reserved, ip.is_unspecified)):
            raise UnsafeSourceURL('Private or local network URLs are blocked.')


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urljoin(req.full_url, newurl)
        _validate_public_url(target)
        return super().redirect_request(req, fp, code, msg, headers, target)


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title_parts = []
        self.meta = {}
        self.canonical = ''

    def handle_starttag(self, tag, attrs):
        attrs = {str(k).lower(): (v or '') for k, v in attrs}
        tag = tag.lower()
        if tag == 'title':
            self.in_title = True
        elif tag == 'meta':
            key = (attrs.get('property') or attrs.get('name') or '').lower()
            if key and attrs.get('content') and key not in self.meta:
                self.meta[key] = attrs['content'].strip()
        elif tag == 'link' and 'canonical' in attrs.get('rel', '').lower():
            self.canonical = attrs.get('href', '').strip()

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self):
        return ' '.join(' '.join(self.title_parts).split()).strip()


def _parse_date(value: str | None):
    if not value:
        return None
    value = value.strip()
    dt = parse_datetime(value)
    if not dt:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, dt_timezone.utc)
    return dt


def _quality(*, url, title, publisher, published_at, canonical, author):
    score = 0.20 if urlparse(url).scheme == 'https' else 0.08
    reasons = ['https'] if urlparse(url).scheme == 'https' else ['http_only']
    if title:
        score += 0.20; reasons.append('has_title')
    if publisher:
        score += 0.18; reasons.append('has_publisher')
    if published_at:
        score += 0.18; reasons.append('has_publication_date')
    if canonical:
        score += 0.12; reasons.append('has_canonical')
    if author:
        score += 0.12; reasons.append('has_author_metadata')
    return round(min(score, 1.0), 3), reasons


def inspect_source(url: str) -> dict:
    _validate_public_url(url)
    req = Request(url, headers={'User-Agent': 'ProofBot/0.4 (+source-metadata-check)'})
    opener = build_opener(_SafeRedirect())
    with opener.open(req, timeout=TIMEOUT) as resp:
        final_url = resp.geturl()
        _validate_public_url(final_url)
        ctype = (resp.headers.get('Content-Type') or '').lower()
        if 'text/html' not in ctype and 'application/xhtml+xml' not in ctype:
            raise ValueError('Source is not an HTML page.')
        raw = resp.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raw = raw[:MAX_BYTES]
        charset = resp.headers.get_content_charset() or 'utf-8'
    html = raw.decode(charset, errors='replace')
    parser = _MetaParser(); parser.feed(html)
    m = parser.meta
    title = (m.get('og:title') or m.get('twitter:title') or parser.title)[:300]
    publisher = (m.get('og:site_name') or m.get('application-name') or '')[:200]
    author = m.get('author') or m.get('article:author') or ''
    published = _parse_date(m.get('article:published_time') or m.get('date') or m.get('datepublished') or m.get('publish-date'))
    domain = (urlparse(final_url).hostname or '').lower()[:255]
    canonical = urljoin(final_url, parser.canonical) if parser.canonical else ''
    score, reasons = _quality(url=final_url, title=title, publisher=publisher or domain, published_at=published, canonical=canonical, author=author)
    return {
        'final_url': final_url,
        'title': title,
        'publisher': publisher or domain,
        'domain': domain,
        'published_at': published,
        'quality_score': score,
        'quality_reasons': reasons,
    }
