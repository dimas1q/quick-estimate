import random


def generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"
