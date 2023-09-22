def foo(x, y=[]):
    y.append(x)
    print(y)


def bar(x="hello"):
    print(x)


def baz(x={"foo": 42}, y=set()):
    print(x)
    print(y)
