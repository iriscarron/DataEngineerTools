import re
from html.parser import HTMLParser
from urllib.parse import urlparse


def remove_extra_spaces(text: str) -> str:
    """
    supprime ts les espaces superflus d'une string
    
    args:
        text: la string avec potentiellement des espaces en trop
        
    returns:
        la string avec les espaces superflus enleves
        
    exemples:
        >>> remove_extra_spaces("Hello    world")
        'Hello world'
        >>> remove_extra_spaces("  Multiple   spaces   here  ")
        'Multiple spaces here'
    """
    # remplace les espaces multiples par un seul espace et enleve les espaces de debut/fin
    return ' '.join(text.split())


def html_to_text(html_string: str) -> str:
    """
    convertit une string html en texte en enlevant les balises et caracteres speciaux
    
    args:
        html_string: la string html a convertir
        
    returns:
        string de texte sans balises html ni caracteres speciaux
        
    exemples:
        >>> html_to_text("<p>Hello <b>world</b>!</p>")
        'Hello world!'
        >>> html_to_text("<div>Test &nbsp; with &amp; entities</div>")
        'Test with & entities'
    """
    # cree un parser html custom pr extraire le texte
    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            
        def handle_data(self, data):
            self.text_parts.append(data)
            
        def get_text(self):
            return ''.join(self.text_parts)
    
    # parse le html et extrait le texte
    parser = TextExtractor()
    parser.feed(html_string)
    text = parser.get_text()
    
    # decode les entites html
    import html
    text = html.unescape(text)
    
    # enleve les espaces superflus
    text = remove_extra_spaces(text)
    
    return text


def extract_domain(url: str) -> str:
    """
    extrait le nom de domaine d'une url
    
    args:
        url: la string url pr extraire le domaine
        
    returns:
        le nom de domaine (netloc) de l'url
        
    exemples:
        >>> extract_domain("https://www.example.com/path/to/page")
        'www.example.com'
        >>> extract_domain("http://subdomain.example.org:8080/test?param=value")
        'subdomain.example.org:8080'
        >>> extract_domain("ftp://files.example.net/file.txt")
        'files.example.net'
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc


# tests et exemples
if __name__ == "__main__":
    print("=" * 60)
    print("test 1: remove_extra_spaces()")
    print("=" * 60)
    
    test1 = "Hello    world   from    Python"
    print(f"Input:  '{test1}'")
    print(f"Output: '{remove_extra_spaces(test1)}'")
    print()
    
    test2 = "  Multiple   spaces   everywhere  "
    print(f"Input:  '{test2}'")
    print(f"Output: '{remove_extra_spaces(test2)}'")
    print()
    
    print("=" * 60)
    print("test 2: html_to_text()")
    print("=" * 60)
    
    html1 = "<p>Hello <b>world</b>!</p>"
    print(f"Input:  {html1}")
    print(f"Output: {html_to_text(html1)}")
    print()
    
    html2 = "<div>Test &nbsp; with &amp; entities and <span>nested</span> tags</div>"
    print(f"Input:  {html2}")
    print(f"Output: {html_to_text(html2)}")
    print()
    
    html3 = """
    <html>
        <body>
            <h1>Title</h1>
            <p>This is a    paragraph with   extra spaces.</p>
            <p>Special chars: &lt; &gt; &amp; &quot;</p>
        </body>
    </html>
    """
    print(f"Input:  {html3[:50]}...")
    print(f"Output: {html_to_text(html3)}")
    print()
    
    print("=" * 60)
    print("test 3: extract_domain()")
    print("=" * 60)
    
    url1 = "https://www.example.com/path/to/page"
    print(f"Input:  {url1}")
    print(f"Output: {extract_domain(url1)}")
    print()
    
    url2 = "http://subdomain.example.org:8080/test?param=value"
    print(f"Input:  {url2}")
    print(f"Output: {extract_domain(url2)}")
    print()
    
    url3 = "https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse"
    print(f"Input:  {url3}")
    print(f"Output: {extract_domain(url3)}")
    print()
    
    url4 = "ftp://files.example.net/downloads/file.zip"
    print(f"Input:  {url4}")
    print(f"Output: {extract_domain(url4)}")
