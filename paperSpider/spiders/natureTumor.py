#!/usr/bin/env python
import scrapy

from paperSpider.items import PaperspiderItem


class NaturetumorSpider(scrapy.Spider):
    name = "natureTumor"
    allowed_domains = ["www.nature.com"]
    start_urls = ["https://www.nature.com/search?q=spatial&subject=cancer&date_range=last_7_days"]
	# https://www.nature.com/search?q=tumor&date_range=today&order=relevance

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url = url,
                                 callback = self.parse)

    def parse(self, response):
        eventObjs = response.xpath("/html/body/div[2]/div/form/section/div/ul/li")
        n = 0
        for eventObj in eventObjs:
            n = n + 1
            if n < 6:
                eventRefSuffix = eventObj.xpath("./div/article/div[1]/div[2]/h3/a/@href").get()
                eventRef = "https://www.nature.com{}".format(eventRefSuffix)
                yield scrapy.Request(url = eventRef, callback = self.sub_parse)
        pass

    def sub_parse(self, response):

        paperItem = PaperspiderItem()

        status_text = response.xpath("//ul[@class='c-article-identifiers']//text()").getall()
        paperItem["url"] = response.url
        paperItem["status"] = " ".join([ s.strip("\n ") for s in status_text if len(s.strip("\n ")) > 0])
        paperItem["title"] = response.xpath("//h1[@class='c-article-title']/text()").get()
        authors = response.xpath("//a[@data-test='author-name']/text()").getall()
        if len(authors) > 1:
            paperItem["authors"]= " ".join([authors[0], authors[-1]])
        else:
            paperItem["authors"]= authors
        paperItem["content"] = " ".join(response.xpath("//*[@id='Abs1-section']//text()").getall())
        paperItem["chatGPT"] = ""
        paperItem["journal" ]= response.xpath("//i[@data-test='journal-title']/text()").get()
        # self.logger.info(paperItem["content"])

        if len(paperItem["content"].strip()) > 0:
            yield paperItem
