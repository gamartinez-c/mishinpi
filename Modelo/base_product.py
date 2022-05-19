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
        self.costs.append(Cost(sale.date, 'Mercado_Pago', 0.02*self.price))
        self.costs.append(Cost(sale.date, 'Shopify', 0.02*self.price))
        self.costs.append(Cost(sale.date, 'product_cost', self.cost * sale.quantity))

    def get_average_costs(self):
        costs_list_dict = {cost.reason: [] for cost in self.costs}
        for cost in self.costs:
            costs_list_dict[cost.reason].append(cost.amount)
        average_costs = {cost_reason: mean(cost_amount_list) for cost_reason, cost_amount_list in costs_list_dict.items()}
        return average_costs

    def get_average_sale_price(self):
        sale_prices = [sale.amount_price for sale in self.sales]
        if len(sale_prices) > 0:
            return mean(sale_prices)
        return 0

    def get_perc_margin(self):
        average_price = self.get_average_sale_price()

        average_costs_dict = self.get_average_costs()
        average_total_cost = sum(average_costs_dict.values())

        return (average_price - average_total_cost)/average_price

    def plot_average_costs(self):
        average_price = self.get_average_sale_price()
        average_costs_dict = self.get_average_costs()

        acumulative_costs = 0
        bar_widths = 0.5

        fig, ax = plt.subplots()
        for cost_reason, cost_amount in average_costs_dict.items():
            ax.bar(
                1, cost_amount,
                bottom=acumulative_costs,
                width=bar_widths,
                color='red',
                label=cost_reason, edgecolor='b')
            acumulative_costs += cost_amount

        margin = average_price - acumulative_costs
        if margin > 0:
            ax.bar(
                1, margin,
                bottom=acumulative_costs,
                width=bar_widths,
                label='margen',
                color='green',
                edgecolor='b')

        ax.hlines(average_price, 1 - bar_widths, 1 + bar_widths, color='black')
        plt.legend()
        plt.show()


