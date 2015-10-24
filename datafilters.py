"""Filters to modify how data is presented"""

output_filters = {}

def outputfilter(func):
    """Decorator that adds this function to the list of output filters"""
    output_filters[func.__name__] = func
    return func

@outputfilter
def human_bytes(value):
    int_value = int(value)
    if int_value > 1024**3:
        size_divisor = 1024**3
        size_symbol = "GB"
    elif int_value > 1024**2:
        size_divisor = 1024**2
        size_symbol = "MB"
    elif int_value > 1024:
        size_divisor = 1024
        size_symbol = "KB"
    else:
        size_divisor = '1'
        size_symbol = ''
    return str(int_value // size_divisor) + size_symbol
