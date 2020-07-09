"""
Representação de um disco adicional uma máquina virtual
"""


class VMDisco:
    def __init__(self, tipo, nome_arquivo, tamanho_mb, tamanho_tipo, caminho_arquivo=None):
        self.tipo = tipo
        self.nome_arquivo = nome_arquivo
        self.tamanho_mb = tamanho_mb
        self.tamanho_tipo = tamanho_tipo
        self.caminho_arquivo = caminho_arquivo

    def __hash__(self):
        return hash(self.nome_arquivo)

    def __eq__(self, other):
        return isinstance(other, VMDisco) and (self.tipo == other.tipo
                                               and self.nome_arquivo == other.nome_arquivo
                                               and self.tamanho_mb == other.tamanho_mb
                                               and self.tamanho_tipo == other.tamanho_tipo
                                               and self.caminho_arquivo == other.caminho_arquivo)

    def __repr__(self):
        return f'''
                tipo: {self.tipo}
                nome_arquivo: {self.nome_arquivo}
                tamanho_mb: { self.tamanho_mb}
                tamanho_tipo: { self.tamanho_tipo}
                caminho_arquivo: {self.caminho_arquivo}
                '''

    def to_dict(self):
        return {
            'tipo': self.tipo,
            'nome_arquivo': self.nome_arquivo,
            'tamanho_mb': self.tamanho_mb,
            'tamanho_tipo': self.tamanho_tipo,
            'caminho_arquivo': self.caminho_arquivo,
        }
