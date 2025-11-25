import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com"]

    def parse(self, response):
        # Extraire chaque livre
        for book in response.css('article.product_pod'):
            title = book.css('h3 a::attr(title)').extract_first()
            price = book.css('p.price_color::text').extract_first()
            availability = book.css('p.availability::text').extract()[1].strip()
            
            yield {
                'title': title,
                'price': price,
                'availability': availability
            }
