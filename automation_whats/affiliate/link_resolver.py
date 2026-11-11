"""Resolucao de links com allowlist e protecao contra destinos privados."""

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests

from .models import ResolvedLink


class UnsafeUrlError(ValueError):
    """URL fora dos limites aceitos pela automacao."""


class SafeLinkResolver:
    """Segue poucos redirecionamentos e valida cada destino."""

    def __init__(
        self,
        allowed_domains: tuple[str, ...],
        session: requests.Session | None = None,
        timeout: float = 15,
        max_redirects: int = 6,
    ) -> None:
        self._allowed_domains = tuple(domain.lower() for domain in allowed_domains)
        self._session = session or requests.Session()
        self._timeout = timeout
        self._max_redirects = max_redirects

    def resolve(self, url: str) -> ResolvedLink:
        current = url
        chain: list[str] = []
        for _ in range(self._max_redirects + 1):
            self._validate(current)
            chain.append(current)
            response = self._session.get(
                current,
                allow_redirects=False,
                stream=True,
                timeout=self._timeout,
                headers={"User-Agent": "affiliate-link-validator/1.0"},
            )
            try:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("Location")
                    if not location:
                        raise UnsafeUrlError("Redirect without Location header")
                    current = urljoin(current, location)
                    continue
                if response.status_code >= 400:
                    raise ValueError(f"Link returned HTTP {response.status_code}")
                return ResolvedLink(url, current, tuple(chain))
            finally:
                response.close()
        raise UnsafeUrlError("Too many redirects")

    def _validate(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise UnsafeUrlError("Only HTTPS marketplace URLs are accepted")
        host = parsed.hostname.lower()
        if not any(host == domain or host.endswith(f".{domain}") for domain in self._allowed_domains):
            raise UnsafeUrlError("Domain is not allowed")
        try:
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as error:
            raise UnsafeUrlError("Domain could not be resolved") from error
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise UnsafeUrlError("Private or non-global destination blocked")
