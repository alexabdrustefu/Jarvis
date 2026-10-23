import feedparser

class NewsActions:
    """Gestisce il recupero delle notizie principali tramite feed RSS gratuiti."""

    def __init__(self):
        # Usiamo il feed RSS ufficiale di ANSA (Ultime Notizie / Top News)
        self.rss_url = "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml"

    def get_daily_news_summary(self, max_news: int = 3) -> str:
        """Scarica le notizie principali e le converte in un riassunto discorsivo."""
        try:
            feed = feedparser.parse(self.rss_url)
            entries = feed.entries[:max_news]

            if not entries:
                # Fallback su Sky TG24 se ANSA non risponde
                feed = feedparser.parse("https://tg24.sky.it/rss/ultimora.xml")
                entries = feed.entries[:max_news]

            if not entries:
                return "Boss, al momento non sono riuscito a recuperare le notizie del giorno."

            count = len(entries)
            summary = f"Boss, ecco le {count} notizie principali di oggi. "

            for i, entry in enumerate(entries, 1):
                title = entry.title
                
                if i == 1:
                    summary += f"La prima notizia: {title}. "
                elif i == 2:
                    summary += f"La seconda: {title}. "
                elif i == 3:
                    summary += f"La terza: {title}. "
                else:
                    summary += f"E un'altra notizia: {title}. "

            return summary

        except Exception as e:
            return f"Si è verificato un errore durante il recupero delle notizie: {str(e)}"


if __name__ == "__main__":
    # Test rapido del modulo eseguendolo direttamente
    news = NewsActions()
    print(news.get_daily_news_summary())