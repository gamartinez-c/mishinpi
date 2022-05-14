import matplotlib.pyplot as plt

from base_product import BaseProduct
from data_handler import DataHandler
from utils import *

pd.set_option('display.max_columns', None)

if __name__ == '__main__':
    path_to_dollar = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
    path_costs_products = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
    path_general_product_information = 'data/stock/products_28_4_2022.csv'
    orders_path = 'data/orders/orders_export_1.csv'
    path_facebook_ads = 'data/facebook_ads/v1.xlsx'

    data_handler = DataHandler(path_to_dollar, path_costs_products, path_general_product_information, orders_path, path_facebook_ads)
    data_handler.load_data()

    stock_counts = [len(product.stock_movements) if type(product) == Product else 0 for product in Product.products_list]
    max_stock_mov = max(stock_counts)
    index_of_max_stock_mov = stock_counts.index(max_stock_mov)
    product_with_max_mov = Product.products_list[index_of_max_stock_mov]

    plot_rentabilidad()
    product_with_max_mov.plot_average_costs()
    margin_dict = {product: product.get_perc_margin() for product in BaseProduct.base_products_list if len(product.sales) > 0}
    plt.hist(margin_dict.values())
    plt.show()

    print(1)
