"""
A collection of simple math operations
"""

def simple_add(a,b):
    """
    adds two numbers together and returns the result

    Parameters
    ----------
    a : int or float
        The first number to add
    b : int or float
        The second number to add
    Returns
    -------
    int or float
        The sum of a and b
    """
    return a+b

def simple_sub(a,b):
    """
    subtracts the second number from the first

    Parameters
    ----------
    a : int or float
        The number to subtract from
    b : int or float
        The number to subtract

    Returns
    -------
    int or float
        The difference of a and b
    """

    return a-b

def simple_mult(a,b):
    return a*b

def simple_div(a,b):
    return a/b

def poly_first(x, a0, a1):
    return a0 + a1*x

def poly_second(x, a0, a1, a2):
    return poly_first(x, a0, a1) + a2*(x**2)

# Feel free to expand this list with more interesting mathematical operations...
# .....
