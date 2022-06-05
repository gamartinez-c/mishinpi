from difflib import SequenceMatcher
import pandas as pd
import numpy as np
import datetime as dt
import streamlit as st
import itertools
import matplotlib.pyplot as plt

from cost import Cost
from sale import Sale
from product import Product
from base_product import BaseProduct


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def plot_revenue(container):
    col1, col2 = container.columns([3, 1])
    col1.subheader('Global revenue')
    week_or_days = col2.selectbox('Select either weeks or days', options=['D', 'W'])
    max_value = 3 if week_or_days == 'W' else 7
    length_of_unit = col2.slider('Amount of units', min_value=1, max_value=max_value, value=int(max_value / 2), step=1)
    min_cut = str(length_of_unit) + week_or_days

    amount = []
    reason = []
    date = []
    for costo in Cost.costs_list:
        amount.append(costo.amount)
        date.append(costo.date)
        reason.append(costo.reason)

    for sale in Sale.sales_list:
        amount.append(sale.amount_price)
        date.append(sale.date)
        reason.append('sale')
    df = pd.DataFrame({'reason': reason, 'date': date, 'amount': amount})

    # Filter with latest sales data
    max_sale_date = df[df['reason'] == 'sale']['date'].max()
    df = df[df['date'] <= max_sale_date]

    fig, axs = plt.subplots()
    plt.xticks(rotation=-45)
    ax_twin = axs.twinx()
    df['date'] = pd.to_datetime(df['date'])

    net_margin = df[['date', 'reason', 'amount']].copy().groupby(['date', 'reason']).sum().reset_index()
    net_margin['amount'] = np.where(net_margin['reason'] == 'sale', net_margin['amount'], -net_margin['amount'])
    net_margin = net_margin[['date', 'amount']].groupby('date').sum().reset_index()
    net_margin = net_margin.set_index('date').resample(min_cut).amount.sum()
    ax_twin.bar(net_margin.index, net_margin, label='net', color=(net_margin > 0).map({True: 'g', False: 'r'}), alpha=0.5, width=3)

    total_cost = df[df['reason'] != 'sale'].copy()
    total_cost['reason'] = 'total'
    total = total_cost.set_index('date').resample(min_cut).amount.sum()
    axs.plot(total.index, total, label='total_cost', marker='x')

    for reason in df.reason.unique():
        df_for_reason = df[df['reason'] == reason][['date', 'amount']]
        df_for_reason = df_for_reason.set_index('date').resample(min_cut).amount.sum()
        axs.plot(df_for_reason.index, df_for_reason, label=reason, marker='x')

    axs.legend()
    ax_twin.legend()
    col1.write(fig)

    col1.subheader('Total cumulative margin.')
    fig_1, ax_1 = plt.subplots()
    plt.xticks(rotation=-45)
    df['amount'] = np.where(df['reason'] != 'sale', -df['amount'], df['amount'])
    df = df.set_index('date').resample(min_cut).amount.sum().reset_index()
    df = df.groupby('date').sum()
    df['amount'] = df['amount'].cumsum()
    ax_1.plot(df.index, df['amount'], label='total revenue', marker='o')
    axs.plot(total.index, total, label='total_cost', marker='x')
    col1.write(fig_1)


def get_next_break_of_all_products(timedelta_to_consider_demand=None):
    next_break_info_dict = {'name': [], 'break_date': [], 'stock_today': [], 'daily_demand': []}
    for product in Product.products_list:
        next_breaking_date = product.get_next_stock_break(timedelta_to_consider_demand)
        stock = product.get_stock()
        daily_demand = product.get_average_daily_demand_for_stock(timedelta_to_consider_demand)
        next_break_info_dict['name'].append(product.name)
        next_break_info_dict['break_date'].append(next_breaking_date)
        next_break_info_dict['stock_today'].append(stock)
        next_break_info_dict['daily_demand'].append(daily_demand)

    next_break_info_df = pd.DataFrame(next_break_info_dict)
    return next_break_info_df


def get_stock_record_of_time_window(timedelta_to_consider_demand=dt.timedelta(days=60), filter_products=None):
    if filter_products is None:
        filter_products = [*Product.products_by_name]
    next_breaking_stock_dates = get_next_break_of_all_products(timedelta_to_consider_demand)
    next_breaking_stock_dates = next_breaking_stock_dates[['name', 'break_date']].rename(columns={'name': 'product', 'break_date': 'date'})
    next_breaking_stock_dates['stock'] = 0

    all_stock_movements_dates_in_timedelta = set()
    for product in Product.products_list:
        for sale in product.sales:
            if sale.date > (dt.date.today() - timedelta_to_consider_demand):
                all_stock_movements_dates_in_timedelta.add(sale.date)

    all_combination_product_date = itertools.product([Product.products_by_name[name] for name in filter_products], all_stock_movements_dates_in_timedelta)
    stocks_dates_data = {'date': [], 'product': [], 'stock': []}
    for product, date in all_combination_product_date:
        stocks_dates_data['date'].append(date)
        stocks_dates_data['product'].append(product.name)
        stocks_dates_data['stock'].append(product.get_stock(date))

    stocks_dates_data = pd.DataFrame(stocks_dates_data)
    stocks_dates_data = pd.concat([stocks_dates_data, next_breaking_stock_dates], ignore_index=True)
    stocks_dates_data.reset_index(drop=True, inplace=True)

    return stocks_dates_data


def plot_stock(timedelta_to_consider_demand, filter_products):
    stock_records = get_stock_record_of_time_window(timedelta_to_consider_demand, filter_products)
    stock_records = stock_records[(stock_records['date'] <= dt.date.today() + timedelta_to_consider_demand) & (stock_records['date'] >= dt.date.today() - timedelta_to_consider_demand)]
    stock_records.sort_values(by='date', inplace=True)

    fig, ax = plt.subplots()
    plt.xticks(rotation=-45)
    for product in stock_records['product'].unique():
        product_records = stock_records[stock_records['product'] == product]
        ax.plot(product_records['date'], product_records['stock'], label=product)

    ax.vlines(dt.date.today(), 0, stock_records['stock'].max(), colors='black', linestyles=(0, (3, 5, 1, 5)))

    # plt.legend()
    return fig, ax


def buy_calculation(time_laps_until_next_purchase=None, timedelta_to_consider_demand=None):
    if time_laps_until_next_purchase is None:
        time_laps_until_next_purchase = dt.timedelta(days=30)
    next_breaking_df = get_next_break_of_all_products(timedelta_to_consider_demand)

    first_date_for_breaking_product = next_breaking_df['break_date'].min()
    print(first_date_for_breaking_product)
    date_to_buy = first_date_for_breaking_product - dt.timedelta(days=2)
    if date_to_buy < dt.date.today():
        date_to_buy = dt.date.today() + dt.timedelta(days=1)

    days_until_buy = (date_to_buy - dt.date.today()).days

    amount_to_supply_between_buys = next_breaking_df['daily_demand'] * time_laps_until_next_purchase.days
    amount_demanded_util_first_buy = next_breaking_df['daily_demand'] * days_until_buy
    amount_to_buy_per_product = amount_to_supply_between_buys - (next_breaking_df['stock_today'] - amount_demanded_util_first_buy)

    amount_to_buy_per_product = np.around(amount_to_buy_per_product)
    next_breaking_df['amount_to_buy_per_product'] = np.where(amount_to_buy_per_product > 0, amount_to_buy_per_product, 0)

    return next_breaking_df


def hist_margin(container):
    margin_dict = {product: product.get_perc_margin() for product in BaseProduct.base_products_list if len(product.sales) > 0}
    fig, ax = plt.subplots()
    _, _, patches = ax.hist(margin_dict.values(), align="mid", color='blue', edgecolor='black', linewidth=1.2)

    for pp in patches:
        x = (pp._x0*2 + pp._width/2) / 2
        y = pp._height + 0.05
        ax.text(x, y, int(pp._height), color='black')

    container.write(fig)
