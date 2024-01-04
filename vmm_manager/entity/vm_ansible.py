"""
VM Ansible entity.
"""


class VMAnsible:
    def __init__(self, group):
        self.group = group
        self.variaveis = []

    def extrair_dados_vars_dict(self, dict_vars, vm_name):
        lista_nomes_var = []
        for item in dict_vars or {}:
            nome_var = item.get('name')

            if nome_var in lista_nomes_var:
                raise ValueError(
                    (f"Variable '{nome_var}' from Ansible group '{self.group}' "
                     f"already exists in VM '{vm_name}'."))

            lista_nomes_var.append(nome_var)
            ansible_var = VMAnsibleVars(
                nome_var, item.get('value'))

            self.variaveis.append(ansible_var)

    def __hash__(self):
        return hash(self.group)

    def __eq__(self, other):
        return isinstance(other, VMAnsible) and (self.group == other.group
                                                 and self.variaveis == other.variaveis)

    def __repr__(self):
        return f'''
                group: {self.group}
                vars: {self.variaveis}
                '''

    def to_dict(self):
        return {
            'group': self.group,
            'vars': [variavel.to_dict() for variavel in self.variaveis]
        }


class VMAnsibleVars:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __eq__(self, other):
        return isinstance(other, VMAnsibleVars) and (self.name == other.name
                                                     and self.value == other.value)

    def __repr__(self):
        return f'''
                name: {self.name}
                value: {self.value}
                '''

    def to_dict(self):
        return {
            'name': self.name,
            'value': self.value
        }
