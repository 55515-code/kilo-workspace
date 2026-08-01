"""Hello World — minimal example for the Kilo workspace."""


def greet(name: str = "world") -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet("Kilo"))
