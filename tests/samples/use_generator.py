def some(iterable):
    for i in iterable:
        yield i


x = sum([i for i in range(1000)])
y = some([i for i in range(1000)])
