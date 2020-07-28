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

        self.__id_drive = None
        self.__id_disco = None
        self.__bus = None
        self.__lun = None

    def set_parametros_extras_vmm(self, id_drive, id_disco, bus, lun):
        self.__id_drive = id_drive
        self.__id_disco = id_disco
        self.__bus = bus
        self.__lun = lun

    def get_id_disco(self):
        if not self.__id_disco:
            raise ValueError('Disco local não possui ID.')

        return self.__id_disco

    def get_id_drive(self):
        if not self.__id_drive:
            raise ValueError('Disco local não possui ID.')

        return self.__id_drive

    def get_tamanho_tipo_create(self):
        return self.tamanho_tipo.name

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
                id_drive: {self.__id_drive}
                id_disco: {self.__id_disco}
                bus: {self.__bus}
                lun: {self.__lun}
                '''

    def to_dict(self):
        return {
            'tipo': self.tipo.value,
            'arquivo': self.arquivo,
            'tamanho_mb': self.tamanho_mb,
            'tamanho_tipo': self.tamanho_tipo.value,
            'caminho': self.caminho,
            'id_drive': self.__id_drive,
            'id_disco': self.__id_disco,
            'bus': self.__bus,
            'lun': self.__lun
        }
