import itertools
import os
import logging
import requests
import pandas as pd
import datetime as dt
import streamlit as st

from sale import Sale
from dollar import Dollar
from product import Product
from base_product import BaseProduct
from kit import Kit
from cost import Cost

class DataHandler:
    path_to_dollar = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
    path_costs_products = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
    path_facebook_ads = 'data/facebook_ads/v1.xlsx'

    # Shopify API
    basic_url = 'https://cmartinezbidal.myshopify.com'
    basic_extension = '/admin/api/2022-04/shop.json'
    order_list_extension = '/admin/api/2022-04/orders.json?status=any&limit=250&created_at_min=2022-01-01T00:00:00-03:00'
    products_list_extension = '/admin/api/2022-04/products.json'
    header_api = {'X-Shopify-Access-Token': os.environ['TOKE']}

    # Facebook API
    spent_url_facebook = "https://graph.facebook.com/v13.0/act_343691773566320/insights?date_present=this_year&time_increment=1&limit=5000&access_token=" + os.environ['token_API_Facebook']

    def __init__(self):
        self.dollar = None

        self.data_is_loaded = False

    def get_products_and_kits_from_api(self):
        response = requests.get(self.basic_url + self.products_list_extension, headers=self.header_api).json()

        products_dict = {'product_name': [], 'sku': [], 'stock': [], 'price': [], 'fecha': [], 'is_kit': []}
        kits_dict = {'product_name': [], 'sku': [], 'stock': [], 'price': [], 'fecha': [], 'is_kit': []}
        for product in response['products']:
            or_prod = product
            if product['status'] == 'active':
                product['variants'][0]['title'] = product['title']
                product = product['variants'][0]
                if '-' not in product['sku']: 
                    dict_to_append_to = products_dict
                else:
                    dict_to_append_to = kits_dict

                dict_to_append_to['product_name'].append(product['title'])
                dict_to_append_to['sku'].append(product['sku'])
                dict_to_append_to['stock'].append(int(product['inventory_quantity']))
                dict_to_append_to['price'].append(float(product['price']))
                dict_to_append_to['fecha'].append(dt.date.today())
                dict_to_append_to['is_kit'].append(product['sku'] == 'active')

        basic_products = pd.DataFrame(products_dict)
        kits_products = pd.DataFrame(kits_dict)

        return basic_products, kits_products

    def get_orders_from_api(self):
        response = requests.get(self.basic_url + self.order_list_extension, headers=self.header_api).json()

        orders_dict = {'Name': [], 'Subtotal': [], 'Shipping': [], 'Shipping_type': [], 'date': [], 'quantity': [], 'product_name': [], 'sku_name': []}

        for order in response['orders']:
            orders_dict['Name'].append(order['name'])
            orders_dict['Subtotal'].append(float(order['subtotal_price']))
            orders_dict['Shipping'].append(float(order['total_price']) - float(order['subtotal_price']))
            orders_dict['Shipping_type'].append(order['shipping_lines'][0]['code'])
            orders_dict['date'].append(order['created_at'])
            orders_dict['quantity'].append([int(product_information['quantity']) for product_information in order['line_items']])
            orders_dict['product_name'].append([product_information['name'] for product_information in order['line_items']])
            orders_dict['sku_name'].append([product_information['sku'] for product_information in order['line_items']])

        agg_orders = pd.DataFrame(orders_dict)
        agg_orders['date'] = pd.to_datetime(agg_orders['date']).dt.date

        return agg_orders

    def get_facebook_spent_from_api(self):
        response = requests.get(self.spent_url_facebook).json()
        df_facebook_ads = pd.DataFrame(response['data'])
        df_facebook_ads['date_start'] = pd.to_datetime(df_facebook_ads['date_start']).dt.date
        df_facebook_ads['exchange_at_date'] = df_facebook_ads['date_start'].apply(lambda date: self.dollar.get_price_at_date(date))
        df_facebook_ads['spend'] = df_facebook_ads['spend'].astype(float) / df_facebook_ads['exchange_at_date']
        df_facebook_ads['spend'] = df_facebook_ads['spend']*1.60
        df_facebook_ads = df_facebook_ads[['date_start', 'spend']]
        df_facebook_ads = df_facebook_ads.groupby('date_start').sum()
        df_facebook_ads.reset_index(inplace=True)
        for row in df_facebook_ads.itertuples():
            Cost(row.date_start, 'facebook_ads', row.spend)

    def load_data(self):
        logging.info('Start Loading')
        self.load_dollar()
        self.load_products()
        self.load_orders()
        # self.load_stock()
        self.get_facebook_spent_from_api()
        # self.load_facebook_ads()
        self.load_shopify_cost()

        self.data_is_loaded = True
        logging.info('End Loading')

    def load_dollar(self):
        # Loading Dollar Price
        path_to_dollar = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
        dollar_information = pd.read_excel(path_to_dollar, sheet_name='dolar_price')
        dollar_information.rename(columns={'Año': 'year', 'Mes': 'month'}, inplace=True)
        dollar_information['day'] = 1
        dollar_information['date'] = pd.to_datetime(dollar_information[['year', 'month', 'day']]).dt.date
        dollar_information.drop(columns=['year', 'month', 'day'], inplace=True)
        price_date_tuple = [*dollar_information.to_records(index=False)]
        self.dollar = Dollar(price_date_tuple)

    def load_products(self):
        # Loading Products
        path_costs_products = 'data/dolar_&_products_extra_information/informacion productos.xlsx'
        costs_products = pd.read_excel(path_costs_products, sheet_name='products')
        rename_columns_dict = {
            'Solucion Micelar': 'Agua Micelar 3 en 1', 'BB Cream': 'BB. CREAM', 'Serum Hyaluronic HA + B3 + B5': 'Serum Hyaluronic. Filler HA + B5 B3',
            'Crema 360 Antiage': 'Crema Antiage 360°', 'Crema humectante íntimia': 'Crema humectante íntima prebiótica', 'Espuma de limpieza': 'Espuma de Limpieza 3en1',
            'Gel lubricante': 'Gel lubricante íntimo', 'Hydra Age': 'Hydra Age', 'Jabón íntimo': 'Jabón de limpieza íntimo prebiótico', 'Lips Glow': 'Lips Glow',
            'Lips Scrub': 'Lips Scrub', 'Contorno de Ojos (Lineas de Expresion)': 'Líneas de Expresión Antiage', 'Oil Serum Age +': 'OIL SERUM AGE+',
            'Protector solar Corporal': 'Protector Solar FPS50+  Emulsion Corporal', 'Protector solar Facial con color': 'Protector Solar FPS50+ Facial c/color',
            'Serum Redensity': 'Serum Redensity. COLÁGENO', 'Sulderm Hidra Filler Intense': 'Sulderm Hydra Filler Intense',
            'Sulderm Hidra Filler Light': 'Sulderm Hydra Filler Light', 'Ultra Defense': 'Ultra Defense', 'Contorno de Ojos (bolsas y ojeras)': 'Bolsas y Ojeras. Antiage',
            'Crema corporal hidratante': 'CREMA HIDRATANTE CORPORAL SUPREME', 'Protector solar Corporal en Spray': 'Protector Solar FPS50+ Spray Corporal',
        'Protector solar Facial en Spray': 'Protector Solar FPS50+ Spray Facial'
        }
        costs_products['PRODUCTOS'].replace(rename_columns_dict, inplace=True)

        basic_products, kits_products = self.get_products_and_kits_from_api()
        basic_products = basic_products.merge(costs_products, left_on='product_name', right_on='PRODUCTOS', how='inner').drop(columns='PRODUCTOS')
        basic_products.rename(columns={'Costo base U$S': 'cost'}, inplace=True)

        for row in basic_products.itertuples():
            exchange = self.dollar.get_price_at_date(row.fecha)
            product = Product(row.price / exchange, row.cost, row.sku, row.product_name)
            product.stock_at_date_dict[row.fecha] = row.stock

        # Load kits
        for row in kits_products.itertuples():
            sku_composition = [*row.sku.split('-')]
            product_composition_list = [BaseProduct.base_products_by_sku[sku] for sku in sku_composition]
            sum_costs = sum([product.cost for product in product_composition_list])
            exchange = self.dollar.get_price_at_date(row.fecha)
            Kit(row.price / exchange, sum_costs, row.sku, row.product_name, product_composition_list)

    def load_orders(self):
        # Loading Orders
        agg_orders = self.get_orders_from_api()
        agg_orders['exchange_at_date'] = agg_orders['date'].apply(lambda date: self.dollar.get_price_at_date(date))
        agg_orders['Shipping'] = agg_orders['Shipping'] / agg_orders['exchange_at_date']
        agg_orders['Subtotal'] = agg_orders['Subtotal'] / agg_orders['exchange_at_date']
        agg_orders['Shipping'].replace(0, None, inplace=True)
        agg_orders['Shipping'].fillna(agg_orders['Shipping'].mean(), inplace=True)

        for order_row in agg_orders.itertuples():
            total_quantity = sum(order_row.quantity)
            total_original_price = sum([BaseProduct.base_products_by_name[product_name].price * product_quantity for product_name, product_quantity in zip(order_row.product_name, order_row.quantity)])
            for quantity, product_name, sku_name in zip(order_row.quantity, order_row.product_name, order_row.sku_name):
                product = BaseProduct.base_products_by_name[product_name]
                amount_price = (order_row.Subtotal * (quantity * product.price) / total_original_price)
                sale = Sale(amount_price, product, quantity, order_row.date)
                shipment_cost = (order_row.Shipping * quantity) / total_quantity
                product.add_sale(sale, shipment_cost, shipping_type=order_row.Shipping_type)

    def load_stock(self):
        stock_path = 'data/stock/products_28_4_2022.csv'
        stock_data = pd.read_csv(stock_path)
        stock_data = stock_data[['Title', 'Variant SKU', 'Variant Inventory Qty']]
        stock_data.rename(columns={'Title': 'product_name', 'Variant SKU': 'sku_name', 'Variant Inventory Qty': 'stock'}, inplace=True)

        stock_path_split = stock_path.split('.')[0].split('_')
        year = int(stock_path_split[-1])
        month = int(stock_path_split[-2])
        day = int(stock_path_split[-3])
        stock_record_date = dt.datetime(year, month, day).date()

        # Filter only base products
        stock_data = stock_data[~stock_data['sku_name'].str.contains('-')]

        for row in stock_data.itertuples():
            product = BaseProduct.base_products_by_name[row.product_name]
            product.stock_at_date_dict[stock_record_date] = row.stock

    def load_facebook_ads(self):
        # Loading Facebook information
        """path_facebook_ads = 'data/facebook_ads/v1.xlsx'
        facebook_costs = pd.read_excel(path_facebook_ads)
        facebook_costs['days_diff'] = (facebook_costs['Fin del informe'] - facebook_costs['Inicio del informe']).apply(lambda x: x.days) + 1
        facebook_costs['days_diff_as_time_delta'] = facebook_costs['days_diff'].apply(lambda x: [dt.timedelta(days=i) for i in range(x)])
        facebook_costs['Importe gastado (ARS) per day'] = facebook_costs['Importe gastado (ARS)'] / facebook_costs['days_diff']
        facebook_costs = facebook_costs.explode('days_diff_as_time_delta')
        facebook_costs['date'] = (facebook_costs['Inicio del informe'] + facebook_costs['days_diff_as_time_delta']).dt.date
        facebook_costs['exchange_at_date'] = facebook_costs['date'].apply(lambda date: self.dollar.get_price_at_date(date))
        facebook_costs['precio'] = facebook_costs['Importe gastado (ARS) per day'] / facebook_costs['exchange_at_date']
        facebook_costs.drop(columns=['Inicio del informe', 'Fin del informe', 'Impresiones', 'Importe gastado (ARS)', 'days_diff', 'exchange_at_date', 'Importe gastado (ARS) per day', 'days_diff_as_time_delta'], inplace=True)

        for row in facebook_costs.itertuples():
            Cost(row.date, 'facebook_ads', row.precio)"""

        df_ads = pd.read_csv('data/facebook_ads/1-Anuncios-10-abr-2019-10-may-2022.csv')
        df_ads.sort_values(by=['Nombre del anuncio', 'Inicio del informe'], inplace=True)
        df_ads = df_ads[['Inicio del informe', 'Fin del informe', 'Nombre del anuncio', 'Importe gastado (ARS)']]
        df_ads.rename(columns={'Inicio del informe': 'start_date',
                               'Fin del informe': 'end_date',
                               'Nombre del anuncio': 'product_name',
                               'Importe gastado (ARS)': 'price_amount'}, inplace=True)
        replace_values_dict = {'Crema 360': 'Crema Antiage 360°',
                               'Hydra Filler Light': 'Sulderm Hydra Filler Light',
                               'Kit Día': 'Kit Día',
                               'Kit Noche': 'Kit Noche',
                               'Serum Hyaluronic': 'Serum Hyaluronic. Filler HA + B5 B3'}
        df_ads['product_name'].replace(replace_values_dict, inplace=True)
        df_ads['end_date'] = pd.to_datetime(df_ads['end_date']).dt.date
        df_ads['start_date'] = pd.to_datetime(df_ads['start_date']).dt.date

        products_dict_names_and_amount = {product_name: df_ads[df_ads['product_name'] == 'product_name']['price_amount'].sum() for product_name in df_ads.product_name.unique()}
        min_date_info_ads = df_ads.start_date.min()
        max_date_info_ads = df_ads.start_date.max()

        for product_name in products_dict_names_and_amount.keys():
            product = BaseProduct.base_products_by_name[product_name]
            sales_in_laps = []
            for sale in product.sales:
                if (sale.date > min_date_info_ads) and (sale.date < max_date_info_ads):
                    sales_in_laps.append(sale)

            cost_per_sale = products_dict_names_and_amount[product_name]/max(1, len(sales_in_laps))

            if len(sales_in_laps) != 0:
                for sale in sales_in_laps:
                    cost = Cost(sale.date, 'facebook_ads', cost_per_sale)
                    product.costs.append(cost)
            else:
                mid_day = (max_date_info_ads - min_date_info_ads)/2 + min_date_info_ads
                cost = Cost(mid_day, 'facebook_ads', cost_per_sale)
                product.costs.append(cost)

    def load_shopify_cost(self):
        for month, year in itertools.product([*range(4, 13)], [2022]):
            Cost(dt.date(year, month, 1), 'Shopify account', 30)
