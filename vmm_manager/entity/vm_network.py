"""
VM network entity.
"""


class VMNetwork:
    def __init__(self, name, default=False):
        self.name = name
        self.default = default

        self.ips = []

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, VMNetwork) and (self.name == other.name
                                                 and self.default == other.default)

    def __repr__(self):
        return f'''
                name: {self.name}
                default: {self.default}
                ips: {self.ips}
                '''

    def to_dict(self):
        return {
            'name': self.name,
            'default': self.default,
            'ips': self.ips,
        }
