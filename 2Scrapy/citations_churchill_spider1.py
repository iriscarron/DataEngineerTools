import scrapy

class ChurchillQuotesSpider(scrapy.Spider):
    name = "citations de Churchill"
    start_urls = ["http://evene.lefigaro.fr/citations/winston-churchill",]

    def parse(self, response):
        for cit in response.xpath('//div[@class="figsco__quote__text"]'):
            text_value = cit.xpath('a/text()').extract_first()
            if text_value:
                # Retirer TOUS les guillemets : " " " ' ' et les guillemets typographiques
                text_value = text_value.strip().strip('""\'"\'\u201c\u201d').strip()
            yield { 'text' : text_value }