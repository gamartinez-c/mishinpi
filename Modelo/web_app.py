import time

import streamlit as st
from threading import Thread

from dotenv import load_dotenv

load_dotenv()

from utils import *
from data_handler import DataHandler


# @st.cache(allow_output_mutation=True)
def load_data():
    data_handler = DataHandler()
    data_loading_thread = Thread(target=data_handler.load_data)
    data_loading_thread.run()
    return data_handler


if __name__ == '__main__':

    st.sidebar.title('Navigation')
    sidebar_selection = st.sidebar.radio('', options=['Home', 'Margin', 'Stock'])

    if len(Product.products_list) == 0:
        data_handler = load_data()
    else:
        data_handler = DataHandler()
        data_handler.data_is_loaded = True

    if sidebar_selection == 'Home':
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

    if sidebar_selection == 'Margin':
        st.title('Welcome to margin page.')
        container_1 = st.container()
        plot_revenue(container_1)

        st.header("Histogram of margin of all products")
        container_2 = st.container()
        hist_margin(container_2)

        st.header('Cost information')
        product_name_and_margin_list = [(product_name, int(product.get_perc_margin() * 100)) for product_name, product in BaseProduct.base_products_by_name.items()]
        product_name_and_margin_list.sort(key=lambda t: t[1])
        product_selection_name = st.selectbox('Select the product to see margin', [product_name + ' | ' + str(margin) + '%' for product_name, margin in product_name_and_margin_list])
        product_selection_name = product_selection_name.split(' | ')[0]
        fig, ax = BaseProduct.base_products_by_name[product_selection_name].plot_average_costs()
        st.write(fig)

    elif sidebar_selection == 'Stock':
        st.title('Stock Control')
        columns = st.columns(2)
        time_until_next_buy_days = columns[0].slider('Time until next buy in days', 7, 45, 30)
        forecast_window_weeks = columns[1].slider('Time for forecast in weeks', 1, 10, 2)
        st.header('Stock to buy')
        product_to_buy = buy_calculation(dt.timedelta(days=time_until_next_buy_days), dt.timedelta(weeks=forecast_window_weeks))
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
            txt = st.text_area('Order text', text_for_order)
            # st.write('Sentiment:', run_sentiment_analysis(txt))

        st.header('Plot  demand & forecast')
        check_product = {}
        products_labels = [product.name + ' | ' + str(product.get_stock()) for product in Product.products_list]
        filter_products = st.multiselect('Select Products', products_labels, products_labels)
        filter_products = [label.split(' | ')[0] for label in filter_products]
        fig, ax = plot_stock(dt.timedelta(weeks=forecast_window_weeks), filter_products=filter_products)
        st.write(fig)

    else:
        pass
