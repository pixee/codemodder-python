from abc import abstractproperty as ap, abstractclassmethod, abstractstaticmethod, abstractmethod


class A:
    @ap
    def foo(self):
        pass

    @abstractclassmethod
    def hello(cls):
        pass

    @abstractstaticmethod
    def goodbye():
        pass

    @abstractmethod
    def bar(self):
        pass
