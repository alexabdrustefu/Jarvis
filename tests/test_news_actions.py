import unittest
from contextlib import contextmanager

from actions.news_actions import NewsActions


RSS = b'''<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Prima notizia</title></item>
<item><title>Seconda notizia</title></item>
<item><title>Terza notizia</title></item>
</channel></rss>'''


class NewsActionsTests(unittest.TestCase):
    def test_falls_back_to_next_feed_with_explicit_timeout_and_limit(self):
        calls = []

        @contextmanager
        def fetcher(request, timeout):
            calls.append((request.full_url, timeout))
            if len(calls) == 1:
                raise OSError("offline source")
            class Response:
                def read(self, limit):
                    self.asserted_limit = limit
                    return RSS
            yield Response()

        news = NewsActions(feed_urls=("https://first.invalid/rss", "https://second.invalid/rss"),
                           timeout=2.5, fetcher=fetcher)

        with self.assertLogs("actions.news_actions", level="WARNING"):
            result = news.get_daily_news_summary(max_news=2)

        self.assertIn("Prima notizia", result)
        self.assertIn("Seconda notizia", result)
        self.assertNotIn("Terza notizia", result)
        self.assertEqual(calls, [
            ("https://first.invalid/rss", 2.5),
            ("https://second.invalid/rss", 2.5),
        ])

    def test_rejects_non_numeric_limit_without_network_access(self):
        news = NewsActions(fetcher=lambda *_args, **_kwargs: self.fail("unexpected network request"))
        self.assertIn("non è valido", news.get_daily_news_summary("molte"))


if __name__ == "__main__":
    unittest.main()
