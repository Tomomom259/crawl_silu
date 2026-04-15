import scrapy


class XjtvsDocumentItem(scrapy.Item):
    url = scrapy.Field()
    normalized_url = scrapy.Field()
    title = scrapy.Field()
    publish_time = scrapy.Field()
    extracted_text = scrapy.Field()
    cleaned_text = scrapy.Field()
