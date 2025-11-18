import requests
from bs4 import BeautifulSoup
import feedparser
from typing import List, Dict, Optional, Any
import time
import random
from urllib.parse import urlparse, urljoin
import re


class NewsRSSScraper:
    """
    classe pr scraper des articles de news depuis des flux rss
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        """
        init le scraper de news rss
        """
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        genere les headers avec user agent aleatoire
        
        returns:
            dict des headers
        """
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_rss_feeds(self, rss_url: str) -> List[Dict[str, Any]]:
        """
        recupere les entrees d'un flux rss
        
        args:
            rss_url: l'url du flux rss
            
        returns:
            liste de dicts avec les infos des articles du flux rss
        """
        print(f"recuperation du flux rss: {rss_url}")
        
        try:
            # parse le flux rss avec feedparser
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries:
                article = {
                    'titre_rss': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'categorie': self._extract_category(entry),
                    'description_rss': entry.get('summary', ''),
                    'date_publication': entry.get('published', ''),
                }
                articles.append(article)
            
            print(f"  -> {len(articles)} articles trouves dans le flux rss\n")
            return articles
            
        except Exception as e:
            print(f"erreur lors de la recuperation du flux rss: {e}\n")
            return []
    
    def _extract_category(self, entry: Any) -> str:
        """
        extrait la categorie d'une entree rss
        
        args:
            entry: entree feedparser
            
        returns:
            la categorie ou 'general' par defaut
        """
        # cherche dans les tags
        if hasattr(entry, 'tags') and entry.tags:
            return entry.tags[0].get('term', 'general')
        
        # cherche dans la categorie
        if hasattr(entry, 'category'):
            return entry.category
        
        # cherche dans les categories (pluriel)
        if hasattr(entry, 'categories') and entry.categories:
            return entry.categories[0][0] if entry.categories[0] else 'general'
        
        return 'general'
    
    def scrape_article(self, url: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        scrape un article complet depuis son url
        
        args:
            url: l'url de l'article
            timeout: timeout en sec
            
        returns:
            dict avec toutes les infos de l'article
        """
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            article_data = {
                'url': url,
                'domaine': self._extract_domain(url),
                'titre_page': self._extract_page_title(soup),
                'titre_article': self._extract_article_title(soup),
                'texte_principal': self._extract_main_text(soup),
                'images': self._extract_images(soup, url),
            }
            
            return article_data
            
        except Exception as e:
            print(f"  erreur lors du scraping de {url}: {e}")
            return {
                'url': url,
                'domaine': self._extract_domain(url),
                'erreur': str(e)
            }
    
    def _extract_domain(self, url: str) -> str:
        """
        extrait le domaine d'une url
        
        args:
            url: l'url
            
        returns:
            le domaine
        """
        return urlparse(url).netloc
    
    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """
        extrait le titre de la page (balise title)
        
        args:
            soup: objet beautifulsoup
            
        returns:
            le titre de la page
        """
        title = soup.find('title')
        return title.get_text().strip() if title else ''
    
    def _extract_article_title(self, soup: BeautifulSoup) -> str:
        """
        extrait le titre de l'article (h1 ou meta)
        
        args:
            soup: objet beautifulsoup
            
        returns:
            le titre de l'article
        """
        # cherche dans les meta tags og:title
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        # cherche dans les h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # cherche dans d'autres meta tags
        meta_title = soup.find('meta', attrs={'name': 'title'})
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        return ''
    
    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """
        extrait le texte principal de l'article
        
        args:
            soup: objet beautifulsoup
            
        returns:
            le texte principal nettoye
        """
        # enleve les elements non pertinents
        for element in soup(['script', 'style', 'header', 'footer', 'nav', 
                            'aside', 'iframe', 'noscript', 'form', 'button']):
            element.decompose()
        
        # cherche le contenu principal dans des balises courantes
        main_content = None
        
        # essaie de trouver l'article dans des conteneurs communs
        for selector in ['article', 'main', '.article-content', '.post-content', 
                        '.entry-content', '[itemprop="articleBody"]']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # si pas trouve, prend le body
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return ''
        
        # extrait le texte
        text = main_content.get_text(separator=' ', strip=True)
        
        # nettoie le texte
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        nettoie le texte en enlevant les espaces superflus
        
        args:
            text: le texte a nettoyer
            
        returns:
            le texte nettoye
        """
        # enleve les espaces multiples
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # enleve les espaces autour de la ponctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        return text
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        extrait les urls des images de l'article
        
        args:
            soup: objet beautifulsoup
            base_url: l'url de base pr les liens relatifs
            
        returns:
            liste des urls des images
        """
        images = []
        
        # cherche les images dans l'article
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                # ignore les petites images (logos, icones, etc.)
                width = img.get('width')
                height = img.get('height')
                
                # filtre basique sur la taille
                if width and height:
                    try:
                        if int(width) < 100 or int(height) < 100:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                # convertit en url absolue
                absolute_url = urljoin(base_url, src)
                
                # ignore les gifs et les petits fichiers
                if not absolute_url.lower().endswith('.gif'):
                    images.append(absolute_url)
        
        return images[:10]  # limite a 10 images max
    
    def scrape_rss_feed(self, 
                       rss_url: str, 
                       max_articles: int = 10,
                       delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        scrape un flux rss complet avec tous les articles
        
        args:
            rss_url: l'url du flux rss
            max_articles: nb max d'articles a scraper
            delay: delai entre chaque article en sec
            
        returns:
            liste de dicts avec toutes les infos des articles
        """
        # recupere les entrees rss
        rss_entries = self.get_rss_feeds(rss_url)
        
        if not rss_entries:
            return []
        
        # limite le nb d'articles
        rss_entries = rss_entries[:max_articles]
        
        print(f"scraping de {len(rss_entries)} articles...\n")
        
        articles_complets = []
        
        for i, rss_entry in enumerate(rss_entries, 1):
            print(f"[{i}/{len(rss_entries)}] scraping: {rss_entry['url']}")
            
            # scrape l'article complet
            article_data = self.scrape_article(rss_entry['url'])
            
            # fusionne les donnees rss et scraping
            article_complet = {
                **rss_entry,
                **article_data,
            }
            
            articles_complets.append(article_complet)
            
            # delai entre les requetes
            if i < len(rss_entries):
                time.sleep(delay)
        
        print(f"\nscraping termine: {len(articles_complets)} articles recuperes")
        return articles_complets


def display_article(article: Dict[str, Any], index: int = 1):
    """
    affiche un article de facon formatee
    
    args:
        article: dict avec les infos de l'article
        index: numero de l'article
    """
    print(f"\n{'='*80}")
    print(f"article {index}")
    print(f"{'='*80}")
    print(f"url: {article.get('url', 'N/A')}")
    print(f"domaine: {article.get('domaine', 'N/A')}")
    print(f"categorie: {article.get('categorie', 'N/A')}")
    print(f"\ntitre page: {article.get('titre_page', 'N/A')}")
    print(f"titre article: {article.get('titre_article', 'N/A')}")
    
    if article.get('texte_principal'):
        texte = article['texte_principal'][:300]
        if len(article.get('texte_principal', '')) > 300:
            texte += "..."
        print(f"\ntexte principal: {texte}")
    
    if article.get('images'):
        print(f"\nnb d'images: {len(article['images'])}")
        for i, img in enumerate(article['images'][:3], 1):
            print(f"  image {i}: {img}")
        if len(article['images']) > 3:
            print(f"  ... et {len(article['images']) - 3} autres")


def save_articles_to_json(articles: List[Dict[str, Any]], filename: str = 'articles.json'):
    """
    sauvegarde les articles dans un fichier json
    
    args:
        articles: liste des articles
        filename: nom du fichier
    """
    import json
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"\narticles sauvegardes dans {filename}")
    except Exception as e:
        print(f"erreur lors de la sauvegarde: {e}")


# exemple d'utilisation
if __name__ == "__main__":
    print("="*80)
    print("scraper de news depuis flux rss")
    print("="*80)
    print()
    
    # cree une instance du scraper
    scraper = NewsRSSScraper()
    
    # exemples de flux rss
    rss_feeds = {
        'Le Monde - A la une': 'https://www.lemonde.fr/rss/une.xml',
        'Le Monde - International': 'https://www.lemonde.fr/international/rss_full.xml',
        'Le Figaro - Actualites': 'https://www.lefigaro.fr/rss/figaro_actualites.xml',
    }
    
    # choisis un flux
    feed_name = 'Le Monde - A la une'
    feed_url = rss_feeds[feed_name]
    
    print(f"flux selectionne: {feed_name}")
    print(f"url: {feed_url}")
    print()
    
    # scrape les articles
    articles = scraper.scrape_rss_feed(
        rss_url=feed_url,
        max_articles=3,  # limite a 3 articles pr l'exemple
        delay=2.0  # 2 sec entre chaque article
    )
    
    # affiche les resultats
    if articles:
        print("\n" + "="*80)
        print("resultats")
        print("="*80)
        
        for i, article in enumerate(articles, 1):
            display_article(article, i)
        
        # sauvegarde dans un fichier json (optionnel)
        # save_articles_to_json(articles, 'news_articles.json')
    else:
        print("\naucun article recupere")
    
    print("\n" + "="*80)
    print("autres flux rss disponibles:")
    print("="*80)
    for name, url in rss_feeds.items():
        print(f"- {name}: {url}")
