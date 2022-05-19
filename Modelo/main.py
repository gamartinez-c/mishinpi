import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from base_product import BaseProduct
from data_handler import DataHandler
from utils import *

load_dotenv()

pd.set_option('display.max_columns', None)

if __name__ == '__main__':
    path_to_dollar = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
    path_costs_products = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
    path_facebook_ads = 'data/facebook_ads/v1.xlsx'

    basic_url = 'https://cmartinezbidal.myshopify.com'
    basic_extension = '/admin/api/2022-04/shop.json'
    order_list_extension = '/admin/api/2022-04/orders.json?status=any&limit=250&created_at_min=2022-01-01T00:00:00-03:00'
    products_list_extension = '/admin/api/2022-04/products.json'
    header_api = {'X-Shopify-Access-Token': os.environ['TOKE']}    

    data_handler = DataHandler(path_to_dollar, path_costs_products, path_facebook_ads, basic_url, basic_extension, order_list_extension, products_list_extension, header_api)
    data_handler.load_data()

    stock_counts = [len(product.stock_movements) if type(product) == Product else 0 for product in Product.products_list]
    max_stock_mov = max(stock_counts)
    index_of_max_stock_mov = stock_counts.index(max_stock_mov)
    product_with_max_mov = Product.products_list[index_of_max_stock_mov]

    plot_rentabilidad()
    product_with_max_mov.plot_average_costs()
    
    margin_dict = {product: product.get_perc_margin() for product in BaseProduct.base_products_list if len(product.sales) > 0}
    fig, ax = plt.subplots()
    ax.hist(margin_dict.values())
    plt.show()

    print(1)
