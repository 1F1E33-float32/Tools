class DataSizeAttribute:
    def __init__(self, size: int = 4):
        self.size = size

    def __call__(self, func):
        func._data_size = self.size
        return func

    def __repr__(self):
        return f"DataSizeAttribute(size={self.size})"


class PropertyNameAttribute:
    def __init__(self, property_name: str):
        self.property_name = property_name

    def __call__(self, func):
        func._property_name = self.property_name
        return func

    def __repr__(self):
        return f"PropertyNameAttribute(property_name='{self.property_name}')"


__all__ = ["DataSizeAttribute", "PropertyNameAttribute"]
