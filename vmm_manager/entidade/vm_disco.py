"""
Representação de um disco adicional uma máquina virtual
"""


class VMDisco:
    def __init__(self, tipo, arquivo, tamanho_mb, tamanho_tipo, caminho=None):
        self.tipo = tipo
        self.arquivo = arquivo
        self.tamanho_mb = tamanho_mb
        self.tamanho_tipo = tamanho_tipo
        self.caminho = caminho

    def __hash__(self):
        return hash(self.arquivo)

    def __eq__(self, other):
        return isinstance(other, VMDisco) and (self.tipo == other.tipo
                                               and self.arquivo == other.arquivo
                                               and self.tamanho_mb == other.tamanho_mb
                                               and self.tamanho_tipo == other.tamanho_tipo
                                               and self.caminho == other.caminho)

    def __repr__(self):
        return f'''
                tipo: {self.tipo}
                arquivo: {self.arquivo}
                tamanho_mb: { self.tamanho_mb}
                tamanho_tipo: { self.tamanho_tipo}
                caminho: {self.caminho}
                '''

    def to_dict(self):
        return {
            'tipo': self.tipo.value,
            'arquivo': self.arquivo,
            'tamanho_mb': self.tamanho_mb,
            'tamanho_tipo': self.tamanho_tipo.value,
            'caminho': self.caminho,
        }
