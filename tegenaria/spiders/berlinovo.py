# -*- coding: utf-8 -*-
"""A spider to crawl the Berlinovo website."""
import re

from scrapy import Request, Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader

from tegenaria.items import ApartmentItem
from tegenaria.spiders import CleanMixin


class BerlinovoSpider(Spider, CleanMixin):
    """A spider to crawl the Berlinovo website."""

    name = 'berlinovo'
    allowed_domains = ['berlinovo.de']
    start_urls = (
        'https://www.berlinovo.de/en/suche-apartments',
    )
    searched_pages = set()

    def parse(self, response):
        """Parse a search result HTML page.

        @url https://www.berlinovo.de/en/suche-apartments
        @returns items 0 0
        @returns requests 15 15
        """
        for link in LinkExtractor(allow=r'/en/suche-apartments.+page=', unique=True).extract_links(response):
            if link.url not in (self.searched_pages, self.start_urls):
                self.searched_pages.add(link.url)
                yield Request(link.url, callback=self.parse)

        for link in LinkExtractor(allow=r'/en/apartment/', unique=True).extract_links(response):
            yield Request(link.url, callback=self.parse_item)

    def parse_item(self, response):
        """Parse an ad page, with an apartment.

        @url https://www.berlinovo.de/en/apartment/2-room-suite-house-heinrich-heine-stra-e-18-24-berlin-mitte
        @returns items 1 1
        @scrapes url title description location address other neighborhood rooms
        """
        self.shutdown_on_error()
        item = ItemLoader(ApartmentItem(), response=response)
        item.add_value('url', response.url)
        item.add_css('title', 'h1.title::text')
        item.add_xpath('description', '//div[contains(@class, field-name-body)]/div/div[4]/div/div/p/text()')
        item.add_xpath('location', '//div[contains(@class, field-name-field-position)]/div/div[5]/div[2]/div/text()')

        zipcode = response.xpath(
            '//*[@id="block-views-aktuelle-wohnung-block-3"]/div/div/div/div/div[3]/div/span/text()[1]') \
            .extract()[0].strip()
        street = response.xpath(
            '//*[@id="block-views-aktuelle-wohnung-block-3"]/div/div/div/div/div[3]/div/span/text()[2]') \
            .extract()[0].strip()
        item.add_value('address', u'{}, {}'.format(street, zipcode))

        item.add_xpath(
            'equipment',
            '//*[@id="block-views-aktuelle-wohnung-block-3"]/div/div/div/div/div[18]/div/div/ul/li/span/text()')
        item.add_xpath('warm_rent',
                       '//*[@id="block-views-aktuelle-wohnung-block-3"]/div/div/div/div/div[5]/span[2]/text()')

        item.add_xpath('other', '//*[@id="block-views-aktuelle-wohnung-block-3"]/div/div/div/div/div/span/text()')

        item.add_value('neighborhood', response.css('#page-title::text').extract()[0].strip().split('Berlin-')[-1])

        room_list = response.xpath('//*[@id="block-views-aktuelle-wohnung-block-3"]/div/div/div/div/div'
                                   '[contains(@class, views-field-field-rooms-description)]/div/text()').extract()
        item.add_value('rooms', re.findall(r'([0-9]+)', ' '.join(room_list))[0])

        yield item.load_item()
