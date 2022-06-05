class StockMovement:
    stock_movements_list = []

    def __init__(self, product, amount, date, shipping_type):
        self.product = product
        self.amount = amount
        self.date = date
        self.shipping_type = shipping_type

        self.stock_movements_list.append(self)

    def __str__(self):
        return f'amount: {self.amount}'
