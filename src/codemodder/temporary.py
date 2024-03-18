import secrets

secrets.SystemRandom().getrandbits(1)
secrets.SystemRandom().randint(0, 9)  # Sensitive
secrets.SystemRandom().random()  # Sensitive
secrets.SystemRandom().sample(["a", "b"], 1)  # Sensitive
secrets.SystemRandom().choice(["a", "b"])  # Sensitive
secrets.SystemRandom().choices(["a", "b"])  # Sensitive
