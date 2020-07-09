"""
Representação dos dados ansible de uma máquina virtual
"""


class VMAnsible:
    def __init__(self, grupo):
        self.grupo = grupo
        self.variaveis = []

    def extrair_dados_vars_dict(self, dict_vars, nome_vm):
        lista_nomes_var = []
        for item in dict_vars or {}:
            nome_var = item.get('nome')

            if nome_var in lista_nomes_var:
                raise ValueError(
                    (f"Variável '{nome_var}' do grupo ansible '{self.grupo}' "
                     f"referenciada mais de uma vez na VM '{nome_vm}'."))

            lista_nomes_var.append(nome_var)
            ansible_var = VMAnsibleVars(
                nome_var, item.get('valor'))

            self.variaveis.append(ansible_var)

    def __hash__(self):
        return hash(self.grupo)

    def __eq__(self, other):
        return isinstance(other, VMAnsible) and (self.grupo == other.grupo
                                                 and self.variaveis == other.variaveis)

    def __repr__(self):
        return f'''
                grupo: {self.grupo}
                vars: {self.variaveis}
                '''

    def to_dict(self):
        return {
            'grupo': self.grupo,
            'vars': [variavel.to_dict() for variavel in self.variaveis]
        }


class VMAnsibleVars:
    def __init__(self, nome, valor):
        self.nome = nome
        self.valor = valor

    def __eq__(self, other):
        return isinstance(other, VMAnsibleVars) and (self.nome == other.nome
                                                     and self.valor == other.valor)

    def __repr__(self):
        return f'''
                nome: {self.nome}
                valor: {self.valor}
                '''

    def to_dict(self):
        return {
            'nome': self.nome,
            'valor': self.valor
        }
