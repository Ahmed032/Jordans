import scrapy
import re
import math


class JordansSpider(scrapy.Spider):
    name = 'jordans'
 #   allowed_domains = ['https://www.jordanusd.net/product-category/jordans-1/']
  #  start_urls = ['https://www.jordanusd.net/product-category/jordans-1/']
    base_url = 'https://www.jordanusd.net/product-category/jordans-1/page/{}/'

    headers = {
        "authority": "www.jordanusd.net",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        "x-requested-with": "XMLHttpRequest",
        "sec-ch-ua-mobile": "?0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
        "sec-ch-ua-platform": '"Windows"',
        "accept": "*/*",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://www.jordanusd.net/product-category/jordans-1/",
        "accept-language": "en-US,en;q=0.9,ar;q=0.8,en-AU;q=0.7,en-GB;q=0.6,it;q=0.5"
    }
    page = 1

    def start_requests(self):
        yield scrapy.Request(url=self.base_url.format(self.page),
                            headers=self.headers,
                            callback=self.parse_jordans)

    def parse_jordans(self, response):
        items_count = int(math.ceil(int(re.findall(r"\d+", 
                      response.css('p.woocommerce-result-count::text').get())[-1]) / 9))

        for box in response.css('div.product-small.box'):
            url = box.css("div.title-wrapper").css("p.product-title").css("a::attr(href)").get()
            yield(scrapy.Request(url=url,
                                headers=self.headers,
                                callback=self.parse))

        if self.page < items_count:
                self.page += 1
                yield scrapy.Request(url=self.base_url.format(self.page),
                        headers=self.headers,
                        callback=self.parse_jordans)

    def parse(self, response):
        item = {}
        item["Title"] = response.css('h1.entry-title::text').get().strip('\n').strip('\t')
        item["Stars Number"] = response.css('div.woocommerce-product-rating').css('div.star-rating::attr(aria-label)').get()
        item["Reviews Number"] = response.css('a.woocommerce-review-link').css('span.count::text').get()
        item["Price before discount and after"] = response.css('p.product-page-price.price-on-sale').css('span.woocommerce-Price-amount.amount').css('bdi::text'
        ).getall() 
#        currency_symbol = response.css('span.amount').css('span.woocommerce-Price-currencySymbol::text').get()
        if response.css("div.tab-panels").css("h4") == []: #this needs fixing
            try:
                item["Description"] = response.css('div.info-content')[0].css('div.std::text')[1].get() #for https://www.jordanusd.net/product/air-jordans-1-high-university-blue/, doesn't work with -1
            except:
                item["Description"] = response.css('div.info-content')[0].css('div.std::text')[-1].get()
        else:
            item["Description"] = response.css('div.woocommerce-Tabs-panel--description').css("h4::text").get()
            

        try:
            item["Release Date"] = re.search(r'[Rr]eleas.*', item["Describtion"])[0]        
        except:
            pass
        try:
            item["Estimated Shipping Time"] = response.xpath("//text()[contains(.,'Estimated Shipping')]").get().strip("\n").split(":")[-1].strip()
        except:
            pass

        table_rows = response.css('table#product-attribute-specs-table').css('tbody').css('tr')
        if table_rows:
            labels = table_rows.css('th.label::text').getall()
            values = table_rows.css('td.last::text').getall()
            if len(labels) == len(values):
                for index in range(0, len(labels)):
                    item[labels[index]] = values[index]
        else:
            spec_values = [spec.strip("\n") for spec in response.xpath('//*[@id="tab-description"]/div[3]/text()').getall()]
            for sindex, spec_label in enumerate(["Manufacturer", "Release date", "Gender", "Color", "Colorway", "Materials"]):
                if spec_label in spec_values[sindex]:
                    item[spec_label.upper()] = spec_values[sindex].split(spec_label)[-1].strip()


 #       tab_panels_dict = dict(zip(labels,values))
  #      item.update(tab_panels_dict)
        item["URL"] = response.url

        yield item