import time

import pandas as pd
import streamlit as st
from threading import Thread

from dotenv import load_dotenv

import dollar

load_dotenv()

from utils import *
from data_handler import DataHandler


class WebApp:

    def __init__(self):
        self.curret_screen = 'Home'

    def run(self):
        st.sidebar.title('Navigation')
        self.curret_screen = st.sidebar.radio('', options=['Home', 'Margin', 'Stock', 'Campaing'])

        data_handler = DataHandler()
        if len(Product.products_list) == 0:
            data_loading_thread = Thread(target=data_handler.load_data)
            data_loading_thread.run()
        else:
            data_handler.data_is_loaded = True

        if self.curret_screen == 'Home':
            st.title('Home Page')
            st.text('Search in the tool')
            my_bar = st.progress(0)
            for percent_complete in range(20):
                time.sleep(0.1)
                if not data_handler.data_is_loaded:
                    my_bar.progress(percent_complete*5)
                else:
                    my_bar.progress(100)
                    break
            st.write('Data is Loaded.')
        else:
            while not data_handler.data_is_loaded:
                time.sleep(0.1)

        if self.curret_screen == 'Margin':
            self.margin_page()
        elif self.curret_screen == 'Stock':
            self.stock_page()
        elif self.curret_screen == 'Campaing':
            self.campaing_page()
        else:
            pass

    def stock_page(self):
        st.title('Stock Control')
        columns = st.columns(2)
        time_until_next_buy_days = columns[0].slider('Time until next buy in days', 7, 45, 30)
        forecast_window_weeks = columns[1].slider('Time for forecast in weeks', 1, 10, 2)
        st.header('Stock to buy')
        product_to_buy = Product.buy_calculation(dt.timedelta(days=time_until_next_buy_days), dt.timedelta(weeks=forecast_window_weeks))
        product_to_buy.sort_values(by='amount_to_buy_per_product', ascending=False)
        st.dataframe(product_to_buy)
        if st.button('Order to buy'):
            product_to_buy_text = product_to_buy
            product_to_buy_text['amount_to_buy_per_product'] = np.where(product_to_buy_text['amount_to_buy_per_product'] % 6 == 0, product_to_buy_text['amount_to_buy_per_product'],
                                                                        product_to_buy_text['amount_to_buy_per_product'] + (6 - product_to_buy_text['amount_to_buy_per_product'] % 6))
            product_to_buy_text = product_to_buy_text[product_to_buy_text['amount_to_buy_per_product'] > 0]
            text_for_order = ''
            product_to_buy_text.sort_values(by='amount_to_buy_per_product', ascending=False)
            for row in product_to_buy_text.itertuples():
                text_for_order += row.name + ' -- ' + str(row.amount_to_buy_per_product) + '\n'
            st.text_area('Order text', text_for_order)

        st.header('Plot  demand & forecast')
        products_labels = [product.name + ' | ' + str(product.get_stock()) for product in Product.products_list]
        filter_products = st.multiselect('Select Products', products_labels, products_labels[0])
        filter_products = [label.split(' | ')[0] for label in filter_products]
        fig, ax = Product.plot_stock(dt.timedelta(weeks=forecast_window_weeks), filter_products=filter_products)
        st.write(fig)

    def margin_page(self):
        st.title('Welcome to margin page.')

        col1, col2 = st.columns([3, 1])
        col1.subheader('Global revenue')
        week_or_days = col2.selectbox('Select either weeks or days', options=['D', 'W'])
        max_value = 3 if week_or_days == 'W' else 7
        length_of_unit = col2.slider('Amount of units', min_value=1, max_value=max_value, value=int(max_value / 2), step=1)
        min_cut = str(length_of_unit) + week_or_days
        fig, ax = plot_sales_and_costs(min_cut)
        col1.write(fig)

        col1.subheader('Total cumulative margin.')
        fig, ax = plot_cumulative_revenue(min_cut)
        col1.write(fig)

        st.header("Histogram of margin of all products")
        fig, ax = hist_margin()
        st.write(fig)

        st.header('Cost information')
        product_name_and_margin_list = [(product_name, int(product.get_perc_margin() * 100)) for product_name, product in BaseProduct.base_products_by_name.items()]
        product_name_and_margin_list.sort(key=lambda t: t[1])
        product_selection_name = st.selectbox('Select the product to see margin', [product_name + ' | ' + str(margin) + '%' for product_name, margin in product_name_and_margin_list])
        product_selection_name = product_selection_name.split(' | ')[0]
        fig, ax = BaseProduct.base_products_by_name[product_selection_name].plot_average_costs()
        st.write(fig)

        st.subheader('Calculator of optimal Price')
        desire_cost = st.number_input('Desire cost in %', min_value=20, max_value=80, value=30, step=5)
        desire_cost = desire_cost/100
        products_best_price_dict = dict()
        products_best_price_dict['name'] = [product.name for product in Product.products_list]
        products_best_price_dict['current_price'] = [product.price for product in Product.products_list]
        products_best_price_dict['cost'] = [product.get_average_cost() for product in Product.products_list]
        products_best_price_dict['ideal_price'] = [cost/desire_cost for cost in products_best_price_dict['cost']]
        products_best_price = pd.DataFrame(products_best_price_dict)
        products_best_price['diff'] = products_best_price['ideal_price'] - products_best_price['current_price']
        dollar_price_today = dollar.Dollar.exchanger.get_price_at_date(dt.date.today())
        products_best_price['price_in_ARS$'] = products_best_price['ideal_price'].apply(lambda price: int((price*dollar_price_today)/50)*50)
        products_best_price['price_actual_ARS$'] = products_best_price['current_price'].apply(lambda price: int(price*dollar_price_today))
        products_best_price.sort_values(by='diff', ascending=False, inplace=True)
        st.dataframe(products_best_price)

    def campaing_page(self):
        st.title('Campaing Information')
        st.text('This Page is to have some insight on the campaing performance.')
        st.header('Sale counted by Shopify')
