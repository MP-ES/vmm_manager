"""
Representação dos dados ansible de uma máquina virtual
"""


class VMAnsible:
    def __init__(self, grupo):
        self.grupo = grupo
        self.variaveis = {}

    def __repr__(self):
        return '''
                grupo: {}
                vars: {}
                '''.format(self.grupo,
                           self.variaveis)

    def to_dict(self):
        return {
            'grupo': self.grupo,
            'vars': self.variaveis
        }
