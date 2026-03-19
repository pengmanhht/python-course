import simple_math

a = 1
b = 2
c = 3
d = 4

def test_simple_add():
    assert simple_math.simple_add(a,b) == (a+b)


def test_simple_sub():
    assert simple_math.simple_sub(a,b) == (a-b)


def test_simple_mult():
    assert simple_math.simple_mult(a,b) == (a * b)



def test_simple_div():
    assert simple_math.simple_div(a,b) == (a / b)


def test_poly_first():
    assert simple_math.poly_first(a,b,c) == (a*c + b)


def test_poly_second():
    pf = simple_math.poly_first(a,b,c)
    assert simple_math.poly_second(a,b,c,d) == (pf + d * (a**2))
    
