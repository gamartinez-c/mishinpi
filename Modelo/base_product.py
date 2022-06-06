import numpy as np
from statistics import mean
import matplotlib.pyplot as plt

from cost import Cost


class BaseProduct:
    base_products_list = []
    base_products_by_sku = {}
    base_products_by_name = {}

    def __init__(self, price, cost, sku_name, name):
        self.price = price
        self.cost = cost
        self.sku_name = sku_name
        self.name = name
        self.sales = []
        self.costs = []

        BaseProduct.base_products_list.append(self)
        BaseProduct.base_products_by_sku[self.sku_name] = self
        BaseProduct.base_products_by_name[self.name] = self

    def add_sale(self, sale, shipment_cost):
        self.sales.append(sale)
        self.costs.append(Cost(sale.date, 'shipment', shipment_cost))
        self.costs.append(Cost(sale.date, 'Mercado_Pago', 0.1*sale.amount_price))
        self.costs.append(Cost(sale.date, 'Shopify', 0.02*sale.amount_price))
        self.costs.append(Cost(sale.date, 'product_cost', self.cost * sale.quantity))

    def get_average_costs_dict(self):
        costs_list_dict = {cost.reason: [] for cost in self.costs}
        for cost in self.costs:
            costs_list_dict[cost.reason].append(cost.amount)
        average_costs = {cost_reason: mean(cost_amount_list) for cost_reason, cost_amount_list in costs_list_dict.items()}
        return average_costs

    def get_average_cost(self, exclude={'shipment'}):
        average_costs_dict = self.get_average_costs_dict()
        average_costs_dict = {key: val for key, val in average_costs_dict.items() if key not in exclude}
        average_cost = sum(average_costs_dict.values())
        return average_cost

    def get_average_sale_price(self):
        sale_prices = [sale.amount_price for sale in self.sales]
        if len(sale_prices) > 0:
            return mean(sale_prices)
        return self.price

    def get_perc_margin(self):
        average_price = self.price

        average_costs_dict = self.get_average_costs_dict()
        average_total_cost = sum(average_costs_dict.values())

        return (average_price - average_total_cost)/average_price

    def plot_average_costs(self):
        average_price = self.price
        average_costs_dict = self.get_average_costs_dict()

        acumulative_costs = 0
        bar_widths = 0.5

        fig, ax = plt.subplots(figsize=(10, 8))
        average_reason_and_costs_list = [*average_costs_dict.items()]
        average_reason_and_costs_list.sort(key=lambda x: x[1], reverse=True)
        total_cost = sum(average_costs_dict.values())
        high_color_g = 0
        low_color_g = 120
        for cost_reason, cost_amount in average_reason_and_costs_list:
            color_g = low_color_g - (cost_amount/total_cost)*(low_color_g - high_color_g)
            ax.bar(
                1, cost_amount,
                bottom=acumulative_costs,
                width=bar_widths,
                color=(1, color_g/255, 0),
                label=cost_reason,
                edgecolor='black',
                linewidth=2.5
            )
            ax.text(1 + bar_widths/2 + 0.01, acumulative_costs + cost_amount/3,
                    str(round(cost_amount/average_price*100, 1)) + '% ' + cost_reason, color='black', fontsize=9)
            acumulative_costs += cost_amount

        margin = average_price - acumulative_costs
        if margin > 0:
            ax.bar(
                1, margin,
                bottom=acumulative_costs,
                width=bar_widths,
                label='margen',
                color='green',
                edgecolor='black',
                linewidth=2.5
            )
            ax.text(1 + bar_widths / 2 + 0.01, acumulative_costs + margin / 3,
                    str(round(margin / average_price * 100, 1)) + '% margen', color='black', fontsize=9)

        ax.hlines(average_price, 1 - bar_widths/5*4, 1 + bar_widths/5*4, color='black')
        plt.legend(loc=3)

        return fig, ax


