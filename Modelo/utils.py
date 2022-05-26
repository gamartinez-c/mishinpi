from difflib import SequenceMatcher
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt

from cost import Cost
from sale import Sale
from product import Product


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def plot_rentabilidad():
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
    net_margin = net_margin.set_index('date').resample('4D').amount.sum()
    ax_twin.bar(net_margin.index, net_margin, label='net', color=(net_margin > 0).map({True: 'g', False: 'r'}), alpha=0.5, width=3)

    total_cost = df[df['reason'] != 'sale'].copy()
    total_cost['reason'] = 'total'
    total = total_cost.set_index('date').resample('4D').amount.sum()
    axs.plot(total.index, total, label='total_cost', marker='x')

    for reason in df.reason.unique():
        df_for_reason = df[df['reason'] == reason][['date', 'amount']]
        df_for_reason = df_for_reason.set_index('date').resample('4D').amount.sum()
        axs.plot(df_for_reason.index, df_for_reason, label=reason, marker='x')

    axs.legend()
    ax_twin.legend()
    plt.show()

    df['amount'] = np.where(df['reason'] != 'sale', -df['amount'], df['amount'])
    df = df.set_index('date').resample('D').amount.sum().reset_index()
    df = df.groupby('date').sum()
    df['amount'] = df['amount'].cumsum()
    df.plot()
    plt.show()


def get_next_break_of_all_products(timedelta_to_consider_demand=None):
    next_break_info_dict = {'name': [], 'break_date': [], 'stock_today': [], 'daily_demand': []}
    for product in Product.products_list:
        next_breaking_date = product.get_next_stock_break(timedelta_to_consider_demand)
        stock = product.get_stock()
        print(timedelta_to_consider_demand)
        daily_demand = product.get_average_daily_demand(timedelta_to_consider_demand)
        next_break_info_dict['name'].append(product.name)
        next_break_info_dict['break_date'].append(next_breaking_date)
        next_break_info_dict['stock_today'].append(stock)
        next_break_info_dict['daily_demand'].append(daily_demand)

    next_break_info_df = pd.DataFrame(next_break_info_dict)
    return next_break_info_df


def buy_calculation(time_laps_until_next_purchase=None, timedelta_to_consider_demand=None):
    if time_laps_until_next_purchase is None:
        time_laps_until_next_purchase = dt.timedelta(days=30)
    next_breaking_df = get_next_break_of_all_products(timedelta_to_consider_demand)

    first_date_for_breaking_product = next_breaking_df['break_date'].min()
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
