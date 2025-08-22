import asyncio

GLOBAL_CONSTANT = 10


class BaseClass:
    """A base class."""

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name


class DerivedClass(BaseClass):
    """A derived class."""

    CLASS_CONSTANT = 20

    def __init__(self, name, value):
        super().__init__(name)
        self.value = value

    @classmethod
    def create_from_value(cls, value):
        return cls(f"Instance-{value}", value)

    @staticmethod
    def static_method(x, y):
        return x + y

    def calculate_something(self, factor):
        """Calculates something based on value and factor."""
        local_variable = self.value * factor

        def nested_function(a):
            return a * 2

        return nested_function(local_variable)


async def async_function(delay):
    await asyncio.sleep(delay)
    return "Done"


def simple_function(arg1, arg2):
    """A simple function."""
    return arg1 + arg2


lambda_function = lambda x: x * x  # noqa: E731

if __name__ == "__main__":
    instance = DerivedClass("test", 5)
    print(instance.calculate_something(2))
