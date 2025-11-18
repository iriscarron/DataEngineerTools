import requests
from typing import Optional, Dict, Any
import time


class HTTPRequester:
    """
    Classe pr faire des requetes HTTP
    """
    
    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"):
        """
        Init le HTTPRequester avec un UserAgent
        
        Args:
            user_agent: Le UserAgent utilisé pr ttes les requetes
        """
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def get(self, 
            url: str, 
            timeout: float = 10.0, 
            max_retries: int = 3, 
            retry_delay: float = 1.0,
            **kwargs) -> requests.Response:
        """
        Fait une requete GET avec meca de retry
        
        Args:
            url: L'URL a requeter
            timeout: Timeout en sec (par defaut: 10.0)
            max_retries: Nb max de retries (par defaut: 3)
            retry_delay: Delai entre les retries en sec (par defaut: 1.0)
            **kwargs: Args suppl pr requests.get
            
        Returns:
            Objet requests.Response
            
        Raises:
            requests.RequestException: Si tous les retries echouent
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
        Fait une requete POST avec meca de retry
        
        Args:
            url: L'URL a requeter
            timeout: Timeout en sec (par defaut: 10.0)
            max_retries: Nb max de retries (par defaut: 3)
            retry_delay: Delai entre les retries en sec (par defaut: 1.0)
            **kwargs: Args suppl pr requests.post
            
        Returns:
            Objet requests.Response
            
        Raises:
            requests.RequestException: Si tous les retries echouent
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
    
    def _request_with_retry(self,
                           method: str,
                           url: str,
                           timeout: float,
                           max_retries: int,
                           retry_delay: float,
                           current_attempt: int,
                           **kwargs) -> requests.Response:
        """
        Methode recursive pr faire des requetes HTTP avec meca de retry
        
        Args:
            method: Methode HTTP ('GET' ou 'POST')
            url: L'URL a requeter
            timeout: Timeout en sec
            max_retries: Nb max de retries
            retry_delay: Delai entre les retries en sec
            current_attempt: Numero de la tentative actuelle (pr la recursion)
            **kwargs: Args suppl pr requests
            
        Returns:
            Objet requests.Response
            
        Raises:
            requests.RequestException: Si tous les retries echouent
        """
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=timeout, **kwargs)
            elif method == 'POST':
                response = self.session.post(url, timeout=timeout, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except (requests.RequestException, requests.Timeout, requests.ConnectionError) as e:
            if current_attempt < max_retries:
                print(f"Attempt {current_attempt + 1} failed: {str(e)}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                # Appel recursif avec compteur incrementé
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
                print(f"All {max_retries + 1} attempts failed.")
                raise


# Exemple d'utilisation
if __name__ == "__main__":
    # Crée une instance du requester
    requester = HTTPRequester()
    
    # Ex 1: Requete GET simple avec timeout par defaut
    try:
        response = requester.get("https://httpbin.org/get")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Ex 2: Requete GET avec timeout et retries custom
    try:
        response = requester.get(
            "https://httpbin.org/delay/2",
            timeout=5.0,
            max_retries=2
        )
        print(f"\nStatus Code: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Ex 3: Requete POST
    try:
        data = {"key": "value"}
        response = requester.post(
            "https://httpbin.org/post",
            json=data,
            timeout=10.0
        )
        print(f"\nPOST Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Request failed: {e}")
