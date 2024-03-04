from abc import abstractproperty as ap, abstractclassmethod, abstractmethod


class A:
    @ap
    def foo(self):
        pass

    @abstractclassmethod
    def hello(cls):
        pass

    @abstractmethod
    def bar(self):
        pass
