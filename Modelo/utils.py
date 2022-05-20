from difflib import SequenceMatcher
import pandas as pd
import numpy as np
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
    df['date'] = pd.to_datetime(df['date'])
    total_cost = df[df['reason'] != 'sale'].copy()
    total_cost['reason'] = 'total'
    for reason in df.reason.unique():
        df_for_reason = df[df['reason'] == reason][['date', 'amount']]
        df_for_reason = df_for_reason.set_index('date').resample('W').amount.sum()
        df_for_reason.plot(label=reason, ax=axs, marker='x')
    total = total_cost.set_index('date').resample('W').amount.sum()
    total.plot(label='total_cost', ax=axs, marker='x')
    plt.legend()
    plt.show()

    df['amount'] = np.where(df['reason'] != 'sale', -df['amount'], df['amount'])
    df = df.set_index('date').resample('D').amount.sum().reset_index()
    df = df.groupby('date').sum()
    df['amount'] = df['amount'].cumsum()
    df.plot()
    plt.show()
