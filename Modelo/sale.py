class Sale:
    sales_list = []

    def __init__(self, amount_price, product, quantity, date):
        self.amount_price = amount_price
        self.product = product
        self.quantity = quantity
        self.date = date

        Sale.sales_list.append(self)

