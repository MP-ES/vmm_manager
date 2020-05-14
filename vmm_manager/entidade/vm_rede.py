"""
Representação de uma interface de rede de uma máquina virtual
"""


class VMRede:
    def __init__(self, nome, principal=False):
        self.nome = nome
        self.principal = principal

        self.ips = []

    def __hash__(self):
        return hash(self.nome)

    def __eq__(self, other):
        return isinstance(other, VMRede) and (self.nome == other.nome
                                              and self.ips == other.ips
                                              and self.principal == other.principal)

    def __repr__(self):
        return '''
                nome: {}
                principal: {}
                ips: {}
                '''.format(self.nome,
                           self.principal,
                           self.ips)

    def to_dict(self):
        return {
            'nome': self.nome,
            'principal': self.principal,
            'ips': self.ips,
        }
