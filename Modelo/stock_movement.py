class StockMovement:
    def __init__(self, product, amount, date):
        self.product = product
        self.amount = amount
        self.date = date

    def __str__(self):
        return f'amount: {self.amount}'
