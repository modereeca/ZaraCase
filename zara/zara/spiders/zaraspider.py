import scrapy
from pysondb import db
import datetime

db_zara_es = db.getDb("Zara-Es.json")


class ZaraSpider(scrapy.Spider):
    name = "zaraspider"
    start_urls = ['https://www.zara.com/es/']

    def parse(self, response, **kwargs):
        mujer_urls = response.xpath('//*[@id="theme-app"]/div/div/div[1]/div/div/div[2]/nav/div[1]/ul[1]/li/a/@href').getall()
        # hombre_urls = response.xpath('//ul[@class:"layout-categories-category__subcategory-main"/li[2]/@href').getall()
        # şimdilik yorum      all_urls_hombre = response.xpath('//ul[@class:"layout-categories-category__subcategory-main"/li[2]/@href').getall()
        for mujer_url in mujer_urls:
            yield response.follow(mujer_url, callback=self.parse_category, cb_kwargs=dict(gender="woman"))

        # for hombre_url in hombre_urls:
        #    yield response.follow(hombre_url, callback=self.parse_category, cb_kwargs=dict(gender="man"))

    def parse_category(self, response, gender):
        product_links = response.xpath('//div[@class="product-grid-product__figure"]/a/@href').getall()
        for product_link in product_links:
            yield response.follow(product_link, callback=self.parse_product, cb_kwargs=dict(gender=gender))

    def parse_product(self, response, gender):
        current_price = response.xpath('//div[@class="product-detail-info__price-amount price"]/span//span/span/div/span/text()').get()
        if current_price is None:
            current_price = response.xpath('//span[@class="price-old__amount price__amount price__amount-old"]/div/span/text()').get()

        sale_price = response.xpath('//span[@class="price-current__amount"]//text()').get()
        discount_percentage = response.xpath('//*[@id="main"]/article/div[2]/div[1]/div[2]/div/div[1]/div[2]/div/span/span[2]/span[1]/text()[2]').get()
        SKUS_on_stock = response.xpath('//li[@class="size-selector-list__item"]')
        SKUS_max = response.xpath('//ul[@role="listbox"]/li').getall()
        product_id = response.xpath('/html/@id').get().replace("product-", "")
        if len(SKUS_on_stock) > 0:
            currently_in_stock = "yes"
        else:
            currently_in_stock = "no"
        title = response.xpath('//h1[@class="product-detail-info__header-name"]/text()').get()
        description = response.xpath('//div[@class="expandable-text__inner-content"]/p/text()[2]').get()
        retailerid = response.xpath('//div[@class="product-detail-info__actions"]/p/text()').get()
        retailer = "Zara(Es)"
        brand = "Zara"
        images = response.xpath('//div[@class="product-detail-images__frame"]/ul/li/button/div/div/picture/img/@src').getall()
        date = datetime.datetime.now()
        existing = db_zara_es.getByQuery({"Product Id": product_id})

        if len(existing) == 0:
            db_zara_es.add({
                'Product Id': product_id,
                'Original Full Price': current_price,
                'Current Price': current_price,
                'Sale Price': sale_price,
                'Discount Percentage': discount_percentage,
                'SKUS_available': "{}{}{}".format(len(SKUS_on_stock), "/", len(SKUS_max)),
                'Date First Seen': "{}{}{}{}{}".format(date.day, "-", date.month, "-", date.year),
                'Date Last Seen': "{}{}{}{}{}".format(date.day, "-", date.month, "-", date.year),
                'Currently in Stock': currently_in_stock,
                'Title + Description': (title, description),
                'Retailer Id': retailerid.split('|')[-1].strip() if retailerid else None,
                'Retailer': retailer,
                'Brand': brand,
                'Gender': gender,
                'Images': images,
            })
        else:
            print("updating existing...")
            db_zara_es.updateByQuery(db_dataset={"Product Id": product_id}, new_dataset={
                'Current Price': current_price,
                'Sale Price': sale_price,
                'Discount Percentage': discount_percentage,
                'SKUS_available': "{}{}{}".format(len(SKUS_on_stock), "/", len(SKUS_max)),
                'Date Last Seen': "{}{}{}{}{}".format(date.day, "-", date.month, "-", date.year),
                'Currently in Stock': currently_in_stock,
                'Title + Description': (title, description),
                'Retailer Id': retailerid.split('|')[-1].strip() if retailerid else None,
                'Retailer': retailer,
                'Brand': brand,
                'Gender': gender,
                'Images': images})