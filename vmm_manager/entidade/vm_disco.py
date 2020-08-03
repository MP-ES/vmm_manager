"""
Representação de um disco adicional uma máquina virtual
"""
from vmm_manager.entidade.acao import Acao


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

    def get_acao_criar_disco(self, id_vm):
        return Acao('criar_disco_vm',
                    id_vm=id_vm,
                    tipo=self.tipo.value,
                    tamanho_mb=self.tamanho_mb,
                    tamanho_tipo=self.get_tamanho_tipo_create(),
                    arquivo=self.arquivo,
                    caminho=self.caminho)

    def get_acao_excluir_disco(self, id_vm):
        return Acao('excluir_disco_vm',
                    id_vm=id_vm,
                    id_drive=self.get_id_drive())

    def get_acoes_diferenca_disco(self, disco_remoto, id_vm):
        acoes = []

        # Alteração de tipo ou redução de disco exige a recriação
        if ((self.tipo != disco_remoto.tipo) or
                (self.tamanho_mb < disco_remoto.tamanho_mb)):
            acoes.append(disco_remoto.get_acao_excluir_disco(id_vm))
            acoes.append(self.get_acao_criar_disco(id_vm))
        else:
            # Definir alterações TODO
            pass

        return acoes

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
