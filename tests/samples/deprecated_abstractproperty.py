from abc import abstractproperty as ap, abstractmethod


class A:
    @ap
    def foo(self):
        pass

    @abstractmethod
    def bar(self):
        pass
