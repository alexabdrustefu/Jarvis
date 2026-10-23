"""RSS news adapter with bounded responses and explicit network timeouts."""

import logging
from urllib.request import Request, urlopen

import feedparser


LOGGER = logging.getLogger(__name__)


class NewsActions:
    """Fetch a small number of headlines from free RSS sources."""

    DEFAULT_FEEDS = (
        "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml",
        "https://tg24.sky.it/rss/ultimora.xml",
    )

    def __init__(self, feed_urls=None, timeout=6, fetcher=urlopen):
        self.feed_urls = tuple(feed_urls or self.DEFAULT_FEEDS)
        self.timeout = timeout
        self.fetcher = fetcher

    def _entries(self, url):
        request = Request(url, headers={"User-Agent": "JARVIS/1.0 (local assistant)"})
        with self.fetcher(request, timeout=self.timeout) as response:
            payload = response.read(1_000_001)
        if len(payload) > 1_000_000:
            raise ValueError("Il feed RSS supera il limite di 1 MB.")
        return feedparser.parse(payload).entries

    def get_daily_news_summary(self, max_news: int = 3) -> str:
        try:
            limit = max(1, min(int(max_news), 10))
        except (TypeError, ValueError):
            return "Il numero di notizie richiesto non è valido."

        entries = []
        for url in self.feed_urls:
            try:
                entries = self._entries(url)
            except Exception:
                LOGGER.warning("Feed RSS non disponibile: %s", url, exc_info=True)
                continue
            if entries:
                break

        if not entries:
            return "Boss, al momento non sono riuscito a recuperare le notizie del giorno."

        titles = [str(entry.get("title", "")).strip() for entry in entries[:limit]]
        titles = [title for title in titles if title]
        if not titles:
            return "Boss, il feed non contiene titoli leggibili."

        summary = f"Boss, ecco le {len(titles)} notizie principali di oggi. "
        ordinal = ("La prima notizia", "La seconda", "La terza")
        for index, title in enumerate(titles):
            label = ordinal[index] if index < len(ordinal) else "Un'altra notizia"
            summary += f"{label}: {title}. "
        return summary.strip()


if __name__ == "__main__":
    print(NewsActions().get_daily_news_summary())
