import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import random
from urllib.parse import quote_plus


class SearchScraper:
    """
    classe pr scraper les resultats de recherche duckduckgo
    """
    
    # liste de user agents pr eviter le blocage
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        """
        init le scraper duckduckgo
        """
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        genere les headers pr la requete avec user agent aleatoire
        
        returns:
            dict des headers
        """
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://duckduckgo.com/',
        }
    
    def search(self, 
               query: str, 
               num_results: int = 10,
               timeout: float = 10.0) -> List[Dict[str, str]]:
        """
        recherche une requete sur duckduckgo et recupere les resultats
        
        args:
            query: la requete de recherche
            num_results: nb de resultats a recuperer (defaut: 10)
            timeout: timeout en sec (defaut: 10.0)
            
        returns:
            liste de dicts avec titre, lien et description de chaque resultat
        """
        # encode la requete pr l'url
        encoded_query = quote_plus(query)
        
        # url de recherche duckduckgo
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        print(f"recherche: {query}")
        print(f"url: {url}")
        print()
        
        try:
            # fait la requete avec les headers
            response = self.session.get(url, headers=self._get_headers(), timeout=timeout)
            response.raise_for_status()
            
            # parse le html avec beautifulsoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # extrait les resultats
            results = self._extract_results(soup)
            
            return results[:num_results]
            
        except requests.RequestException as e:
            print(f"erreur lors de la requete: {e}")
            return []
    
    def _extract_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        extrait les resultats de recherche du html
        
        args:
            soup: objet beautifulsoup de la page de resultats
            
        returns:
            liste de dicts avec les infos des resultats
        """
        results = []
        
        # duckduckgo html utilise des divs avec la classe 'result' pr chaque resultat
        search_results = soup.find_all('div', class_='result')
        
        for result in search_results:
            try:
                # recupere le titre et le lien
                title_elem = result.find('a', class_='result__a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                link = title_elem.get('href', '')
                
                if not link:
                    continue
                
                # recupere la description (snippet)
                description = ""
                desc_elem = result.find('a', class_='result__snippet')
                
                if desc_elem:
                    description = desc_elem.get_text().strip()
                
                results.append({
                    'titre': title,
                    'lien': link,
                    'description': description
                })
                
            except Exception as e:
                # ignore les resultats qui ne peuvent pas etre parsés
                continue
        
        return results
    
    def search_with_retry(self,
                         query: str,
                         num_results: int = 10,
                         max_retries: int = 3,
                         retry_delay: float = 2.0) -> List[Dict[str, str]]:
        """
        recherche avec meca de retry en cas d'echec
        
        args:
            query: la requete de recherche
            num_results: nb de resultats a recuperer
            max_retries: nb max de tentatives
            retry_delay: delai entre les tentatives en sec
            
        returns:
            liste de dicts avec les resultats
        """
        for attempt in range(max_retries + 1):
            try:
                results = self.search(query, num_results)
                
                if results:
                    return results
                
                if attempt < max_retries:
                    print(f"aucun resultat trouve, retry dans {retry_delay}s...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                if attempt < max_retries:
                    print(f"tentative {attempt + 1} echouee: {e}")
                    print(f"retry dans {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"toutes les tentatives ont echoue")
                    raise
        
        return []


def display_results(results: List[Dict[str, str]]):
    """
    affiche les resultats de recherche de facon formatee
    
    args:
        results: liste de dicts avec les resultats
    """
    if not results:
        print("aucun resultat trouve")
        return
    
    print(f"\n{'='*80}")
    print(f"nb de resultats: {len(results)}")
    print(f"{'='*80}\n")
    
    for i, result in enumerate(results, 1):
        print(f"resultat {i}:")
        print(f"  titre: {result['titre']}")
        print(f"  lien: {result['lien']}")
        if result['description']:
            desc = result['description'][:150]
            if len(result['description']) > 150:
                desc += "..."
            print(f"  description: {desc}")
        print()


# exemple d'utilisation
if __name__ == "__main__":
    print("="*80)
    print("scraper de recherche duckduckgo")
    print("="*80)
    print()
    
    # cree une instance du scraper
    scraper = SearchScraper()
    
    # exemple 1: recherche simple
    print("exemple 1: recherche 'python programming'")
    print("-"*80)
    results = scraper.search_with_retry("python programming", num_results=5)
    display_results(results)
    
    # pause pr eviter d'etre bloque par google
    time.sleep(3)
    
    # exemple 2: autre recherche
    print("\n" + "="*80)
    print("exemple 2: recherche 'data engineering'")
    print("-"*80)
    results = scraper.search_with_retry("data engineering", num_results=5)
    display_results(results)
    
    print("\n" + "="*80)
    print("notes importantes:")
    print("="*80)
    print("- duckduckgo est plus permissif que google pr le scraping")
    print("- il est recommande d'ajouter des delais entre les requetes")
    print("- les selecteurs html peuvent changer")
    print("- rotation des user agents peut aider a eviter les blocages")
