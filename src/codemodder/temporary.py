import random

random.getrandbits(1)
random.randint(0, 9)  # Sensitive
random.random()  # Sensitive
random.sample(["a", "b"], 1)  # Sensitive
random.choice(["a", "b"])  # Sensitive
random.choices(["a", "b"])  # Sensitive
