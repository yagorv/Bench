def calculate_total(price, quantity, tax_rate):
    # Bug: tax is applied per item but quantity is omitted from the taxable amount.
    return round(price + price * tax_rate, 3)
