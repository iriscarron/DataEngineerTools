import requests
from typing import Optional, Dict, Any, List
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


class HTTPRequester:
    """
    classe amelioree pr faire des requetes http avec rotation de user agents et parsing html
    """
    
    # liste de user agents pr la rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0",
    ]
    
    def __init__(self, user_agent: Optional[str] = None):
        """
        init le httprequester avec rotation de user agents
        
        args:
            user_agent: user agent specifique (optionnel, sinon rotation auto)
        """
        self.use_rotation = user_agent is None
        self.user_agent = user_agent
        self.session = requests.Session()
        if not self.use_rotation:
            self.session.headers.update({'User-Agent': self.user_agent})
    
    def _get_random_user_agent(self) -> str:
        """
        retourne un user agent aleatoire de la liste
        
        returns:
            un user agent aleatoire
        """
        return random.choice(self.USER_AGENTS)
    
    def get(self, 
            url: str, 
            timeout: float = 10.0, 
            max_retries: int = 3, 
            retry_delay: float = 1.0,
            **kwargs) -> requests.Response:
        """
        fait une requete get avec meca de retry
        
        args:
            url: l'url a requeter
            timeout: timeout en sec (par defaut: 10.0)
            max_retries: nb max de retries (par defaut: 3)
            retry_delay: delai entre les retries en sec (par defaut: 1.0)
            **kwargs: args suppl pr requests.get
            
        returns:
            objet requests.response
            
        raises:
            requests.requestexception: si tous les retries echouent
        """
        return self._request_with_retry(
            method='GET',
            url=url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            current_attempt=0,
            **kwargs
        )
    
    def post(self, 
             url: str, 
             timeout: float = 10.0, 
             max_retries: int = 3,
             retry_delay: float = 1.0,
             **kwargs) -> requests.Response:
        """
        fait une requete post avec meca de retry
        
        args:
            url: l'url a requeter
            timeout: timeout en sec (par defaut: 10.0)
            max_retries: nb max de retries (par defaut: 3)
            retry_delay: delai entre les retries en sec (par defaut: 1.0)
            **kwargs: args suppl pr requests.post
            
        returns:
            objet requests.response
            
        raises:
            requests.requestexception: si tous les retries echouent
        """
        return self._request_with_retry(
            method='POST',
            url=url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            current_attempt=0,
            **kwargs
        )
    
    def get_soup(self, 
                 url: str, 
                 timeout: float = 10.0, 
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 parser: str = 'html.parser') -> BeautifulSoup:
        """
        recupere l'objet beautifulsoup d'une url
        
        args:
            url: l'url a parser
            timeout: timeout en sec (par defaut: 10.0)
            max_retries: nb max de retries (par defaut: 3)
            retry_delay: delai entre les retries en sec (par defaut: 1.0)
            parser: le parser a utiliser (par defaut: 'html.parser')
            
        returns:
            objet beautifulsoup
        """
        response = self.get(url, timeout=timeout, max_retries=max_retries, retry_delay=retry_delay)
        return BeautifulSoup(response.content, parser)
    
    def _request_with_retry(self,
                           method: str,
                           url: str,
                           timeout: float,
                           max_retries: int,
                           retry_delay: float,
                           current_attempt: int,
                           **kwargs) -> requests.Response:
        """
        methode recursive pr faire des requetes http avec meca de retry
        
        args:
            method: methode http ('get' ou 'post')
            url: l'url a requeter
            timeout: timeout en sec
            max_retries: nb max de retries
            retry_delay: delai entre les retries en sec
            current_attempt: numero de la tentative actuelle (pr la recursion)
            **kwargs: args suppl pr requests
            
        returns:
            objet requests.response
            
        raises:
            requests.requestexception: si tous les retries echouent
        """
        # rotation du user agent si activee
        if self.use_rotation:
            self.session.headers.update({'User-Agent': self._get_random_user_agent()})
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=timeout, **kwargs)
            elif method == 'POST':
                response = self.session.post(url, timeout=timeout, **kwargs)
            else:
                raise ValueError(f"methode http non supportee: {method}")
            
            response.raise_for_status()
            return response
            
        except (requests.RequestException, requests.Timeout, requests.ConnectionError) as e:
            if current_attempt < max_retries:
                print(f"tentative {current_attempt + 1} echouee: {str(e)}. retry dans {retry_delay}s...")
                time.sleep(retry_delay)
                # appel recursif avec compteur incremente
                return self._request_with_retry(
                    method=method,
                    url=url,
                    timeout=timeout,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    current_attempt=current_attempt + 1,
                    **kwargs
                )
            else:
                print(f"toutes les {max_retries + 1} tentatives ont echoue.")
                raise


class HTMLParser:
    """
    classe pr parser du html et extraire les infos principales
    """
    
    def __init__(self, requester: Optional[HTTPRequester] = None):
        """
        init le parser html
        
        args:
            requester: instance de httprequester (optionnel, en cree une si none)
        """
        self.requester = requester or HTTPRequester()
    
    def parse_page(self, url: str) -> Dict[str, Any]:
        """
        parse une page html et recupere les infos principales
        
        args:
            url: l'url de la page a parser
            
        returns:
            dict avec titre, h1, images, liens sortants et texte principal
        """
        soup = self.requester.get_soup(url)
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        return {
            'titre': self.get_title(soup),
            'h1': self.get_h1_tags(soup),
            'images': self.get_image_links(soup, base_url),
            'liens_sortants': self.get_external_links(soup, base_url),
            'texte_principal': self.get_main_text(soup)
        }
    
    def get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """
        recupere le titre de la page
        
        args:
            soup: objet beautifulsoup
            
        returns:
            le titre de la page ou none
        """
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else None
    
    def get_h1_tags(self, soup: BeautifulSoup) -> List[str]:
        """
        recupere tous les h1 de la page
        
        args:
            soup: objet beautifulsoup
            
        returns:
            liste des textes des h1
        """
        h1_tags = soup.find_all('h1')
        return [h1.get_text().strip() for h1 in h1_tags]
    
    def get_image_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        recupere tous les liens vers les images
        
        args:
            soup: objet beautifulsoup
            base_url: l'url de base pr les liens relatifs
            
        returns:
            liste des urls des images
        """
        images = soup.find_all('img')
        image_links = []
        
        for img in images:
            src = img.get('src')
            if src:
                # convertit les liens relatifs en liens absolus
                absolute_url = urljoin(base_url, src)
                image_links.append(absolute_url)
        
        return image_links
    
    def get_external_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        recupere tous les liens sortants vers d'autres sites
        
        args:
            soup: objet beautifulsoup
            base_url: l'url de base pr filtrer les liens internes
            
        returns:
            liste des urls externes
        """
        links = soup.find_all('a', href=True)
        external_links = []
        base_domain = urlparse(base_url).netloc
        
        for link in links:
            href = link.get('href')
            if href:
                # convertit les liens relatifs en liens absolus
                absolute_url = urljoin(base_url, href)
                link_domain = urlparse(absolute_url).netloc
                
                # verifie si le lien est externe
                if link_domain and link_domain != base_domain:
                    external_links.append(absolute_url)
        
        return list(set(external_links))  # deduplique
    
    def get_main_text(self, soup: BeautifulSoup) -> str:
        """
        recupere le texte principal de la page
        
        args:
            soup: objet beautifulsoup
            
        returns:
            le texte principal de la page
        """
        # enleve les scripts et styles
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()
        
        # recupere le texte
        text = soup.get_text(separator=' ', strip=True)
        
        # nettoie les espaces multiples
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text


# exemple d'utilisation
if __name__ == "__main__":
    print("=" * 80)
    print("test de la classe httprequester amelioree avec rotation de user agents")
    print("=" * 80)
    print()
    
    # cree une instance avec rotation de user agents
    requester = HTTPRequester()
    
    # test de rotation de user agents
    print("test rotation user agents:")
    for i in range(3):
        ua = requester._get_random_user_agent()
        print(f"  user agent {i+1}: {ua[:50]}...")
    print()
    
    # cree le parser html
    parser = HTMLParser(requester)
    
    # exemple: parser une page
    print("=" * 80)
    print("parsing d'une page exemple")
    print("=" * 80)
    
    try:
        # utilise httpbin pr tester
        test_url = "https://example.com"
        print(f"url: {test_url}")
        print()
        
        result = parser.parse_page(test_url)
        
        print(f"titre: {result['titre']}")
        print()
        
        print(f"nb de h1: {len(result['h1'])}")
        if result['h1']:
            for i, h1 in enumerate(result['h1'], 1):
                print(f"  h1 {i}: {h1}")
        print()
        
        print(f"nb d'images: {len(result['images'])}")
        if result['images']:
            for i, img in enumerate(result['images'][:5], 1):  # affiche que les 5 premieres
                print(f"  image {i}: {img}")
            if len(result['images']) > 5:
                print(f"  ... et {len(result['images']) - 5} autres")
        print()
        
        print(f"nb de liens sortants: {len(result['liens_sortants'])}")
        if result['liens_sortants']:
            for i, link in enumerate(result['liens_sortants'][:5], 1):  # affiche que les 5 premiers
                print(f"  lien {i}: {link}")
            if len(result['liens_sortants']) > 5:
                print(f"  ... et {len(result['liens_sortants']) - 5} autres")
        print()
        
        print(f"texte principal (premiers 200 caracteres):")
        print(f"  {result['texte_principal'][:200]}...")
        
    except Exception as e:
        print(f"erreur lors du parsing: {e}")
