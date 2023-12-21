import scrapy
from pysondb import db
import datetime

# Veritabanı bağlantısı oluşturuluyor
db_zara_es = db.getDb("Zara-Es.json")


class ZaraSpider(scrapy.Spider):
    name = "zaraspider"
    start_urls = ['https://www.zara.com/es/']

    # Ana sayfadan kategori sayfalarına geçiş yapma işlemi
    def parse(self, response, **kwargs):

        # Kadın ve erkek kategorilerinin URL'lerini alma
        mujer_urls = response.xpath('//*[@id="theme-app"]/div/div/div[1]/div/div/div[2]/nav/div[1]/ul[1]/li/a/@href').getall()
        hombre_urls = response.xpath('//*[@id="theme-app"]/div/div/div[1]/div/div/div[2]/nav/div[1]/ul[2]/li/a/@href').getall()

        # Kadın kategorisi için her bir URL'yi takip ederek parse_category fonksiyonuna yönlendirme
        for mujer_url in mujer_urls:
            yield response.follow(mujer_url, callback=self.parse_category, cb_kwargs=dict(gender="Woman"))

        # Erkek kategorisi için her bir URL'yi takip ederek parse_category fonksiyonuna yönlendirme
        for hombre_url in hombre_urls:
            yield response.follow(hombre_url, callback=self.parse_category, cb_kwargs=dict(gender="Man"))

    # Kategori sayfasından ürünlerin bulunduğu sayfalara geçiş yapma işlemi
    def parse_category(self, response, gender):

        # Kategori sayfasındaki ürünlerin URL'lerini alma
        product_links = response.xpath('//div[@class="product-grid-product__figure"]/a/@href').getall()

        # Her bir ürün sayfasına yönlendirme yapma ve parse_product fonksiyonuna yönlendirme
        for product_link in product_links:
            yield response.follow(product_link, callback=self.parse_product, cb_kwargs=dict(gender=gender, product_link=product_link),)

    # Ürün sayfasından ürün detaylarını çıkarma işlemi
    def parse_product(self, response, gender, product_link):

        # Ürün detaylarını çıkarmak için kullanılan XPath ifadeleri
        product_id = response.xpath('/html/@id').get().replace("product-", "")
        original_full_price = response.xpath('//div[@class="product-detail-info__price-amount price"]/span//span/span/div/span/text()').get()
        current_price = response.xpath('//span[@class="price-old__amount price__amount price__amount-old"]/div/span/text()').get()
        sale_price = response.xpath('//span[@class="price-current__amount"]//text()').get()
        discount_percentage = response.xpath('//span[@class="price-current__discount-percentage"]/text()[2]').get()
        SKUS_on_stock = response.xpath('//li[@class="size-selector-list__item"]')
        SKUS_max = response.xpath('//ul[@role="listbox"]/li').getall()
        if len(SKUS_on_stock) > 0:
            currently_in_stock = "Yes"
        else:
            currently_in_stock = "No"
        title = response.xpath('//h1[@class="product-detail-info__header-name"]/text()').get()
        description = response.xpath('//div[@class="expandable-text__inner-content"]/p/text()[2]').get()
        retailerid = response.xpath('//div[@class="product-detail-info__actions"]/p/text()').get()
        if retailerid is None:
            retailerid = response.xpath('//p[@class="product-color-extended-name product-detail-color-selector__selected-color-name"]/text()')
        retailer = "Zara(Es)"
        brand = "Zara"
        images = response.css('.media-image__image::attr(src)').getall()
        date = datetime.datetime.now()
        existing = db_zara_es.getByQuery({"Product Id": product_id})
        if discount_percentage is None:
            sale_price = None
            current_price = original_full_price
        if original_full_price is not None:

            # Ürün detaylarını çıkardıktan sonra eksik bilgileri doldurarak veri tabanına ekleme veya güncelleme işlemi
            if len(existing) == 0:
                db_zara_es.add({
                    'Product Id': product_id,
                    'Original Full Price': original_full_price,
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
                    'Product Link': product_link
                })
            else:
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
                    'Images': images,
                    'Product Link': product_link})
