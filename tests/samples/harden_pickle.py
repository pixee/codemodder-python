import pickle

try:
    data = pickle.load(open("some.pickle", "rb"))
except FileNotFoundError:
    data = None
