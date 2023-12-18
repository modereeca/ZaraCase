import scrapy
from pysondb import db
import datetime

db_zara_es = db.getDb("Zara-Es.json")

class ZaraSpider(scrapy.Spider):
    name = "zaraspider"
    start_urls = [
        'https://www.zara.com/es/es/mujer-prendas-exterior-l1184.html?v1=2290701&page=1',
        'https://www.zara.com/es/es/mujer-prendas-exterior-l1184.html?v1=2290701&page=2',
        'https://www.zara.com/es/es/mujer-prendas-exterior-l1184.html?v1=2290701&page=3',
        'https://www.zara.com/es/es/mujer-prendas-exterior-l1184.html?v1=2290701&page=4',
        'https://www.zara.com/es/es/mujer-prendas-exterior-l1184.html?v1=2290701&page=5',

    ]

    def parse(self, response):
        product_links = response.xpath('//div[@class="product-grid-product__figure"]/a/@href').getall()

        for product_link in product_links:
            yield response.follow(product_link, callback=self.parse_product)

    def parse_product(self, response):
        original_full_price = response.xpath('//div[@class="product-detail-info__price-amount price"]/span//span/span/div/span/text()').get()
        before_sale_ofp = response.xpath('//div[@class="product-detail-info__price-amount price"]/span/span/span/div/span/text()').get()
        current_price = response.xpath('//span[@class="price-old__amount price__amount price__amount-old"]/div/span/text()').get()
        sale_price = response.xpath('//span[@class="price-current__amount"]//text()').get()
        discount_percentage = response.xpath('//*[@id="main"]/article/div[2]/div[1]/div[2]/div/div[1]/div[2]/div/span/span[2]/span[1]/text()[2]').get()
        SKUS_on_stock = response.xpath('//li[@class="size-selector-list__item"]')
        SKUS_max = response.xpath('//ul[@role="listbox"]/li').getall()
        product_id = response.xpath('/html/@id').get()
        if len(SKUS_on_stock) > 0:
            currently_in_stock = "yes"
        else:
            currently_in_stock = "no"
        title = response.xpath('//h1[@class="product-detail-info__header-name"]/text()').get()
        description = response.xpath('//div[@class="expandable-text__inner-content"]/p/text()[2]').get()
        retailerid = response.xpath('//div[@class="product-detail-info__actions"]/p/text()').get()
        retailer = "Zara(Es)"
        brand = "Zara"
        gender = response.xpath('/html/head/script[13]/text()').get()
        print(response.body, "****************************************************************")
        images = response.xpath('//div[@class="product-detail-images__frame"]/ul/li/button/div/div/picture/img/@src').getall()
        date = datetime.datetime.now()
        if db_zara_es.getByQuery({"Product Id": product_id}) is None:
            db_zara_es.add({
                'Product Id': product_id.replace("product-", ""),
                'Original Full Price': original_full_price if original_full_price else before_sale_ofp,
                'Current Price': current_price.strip() if current_price else None,
                'Sale Price': sale_price.strip() if sale_price else None,
                'Discount Percentage': discount_percentage.strip() if discount_percentage else None,
                'SKUS_available': "{}{}{}".format(len(SKUS_on_stock), "/", len(SKUS_max)),
                'Date First Seen': "{}{}{}{}{}".format(date.day, "-", date.month, "-", date.year),
                'Date Last Seen': "{}{}{}{}{}".format(date.day, "-", date.month, "-", date.year),
                'Currently in Stock': currently_in_stock,
                'Title + Description': (title, description),
                'Retailer Id': retailerid.split('|')[-1].strip(),
                'Retailer': retailer,
                'Brand': brand,
                'Gender': gender,
                'İmages': images if images else None
            })
        else:
            db_zara_es.updateByQuery(db_dataset={"Product Id": product_id}, new_dataset={
                'Original Full Price': original_full_price if original_full_price else before_sale_ofp,
                'Current Price': current_price.strip() if current_price else None,
                'Sale Price': sale_price.strip() if sale_price else None,
                'Discount Percentage': discount_percentage.strip() if discount_percentage else None,
                'SKUS_available': "{}{}{}".format(len(SKUS_on_stock), "/", len(SKUS_max)),
                'Date Last Seen': "{}{}{}{}{}".format(date.day, "-", date.month, "-", date.year),
                'Currently in Stock': currently_in_stock,
                'Title + Description': (title, description),
                'Retailer Id': retailerid.split('|')[-1].strip(),
                'Retailer': retailer,
                'Brand': brand,
                'Gender': gender,
                'İmages': images if images else None})


