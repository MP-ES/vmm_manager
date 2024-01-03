"""
VM additional disk entity.
"""
from vmm_manager.entity.action import Action


class VMDisk:
    def __init__(self, bus_type, file, size_mb, size_type, path=None):
        self.bus_type = bus_type
        self.file = file
        self.size_mb = size_mb
        self.size_type = size_type
        self.path = path

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
        return self.size_type.name

    def get_acao_criar_disco(self, vm_name):
        return Action(
            'criar_disco_vm',
            vm_name=vm_name,
            bus_type=self.bus_type.value,
            size_mb=self.size_mb,
            size_type=self.get_tamanho_tipo_create(),
            file=self.file,
            path=self.path
        )

    def get_acao_excluir_disco(self, id_vm):
        return Action(
            Action.ACAO_EXCLUIR_DISCO_VM,
            id_vm=id_vm,
            id_drive=self.get_id_drive()
        )

    def get_acao_expandir_disco(self, id_vm, id_drive):
        return Action(
            'expandir_disco_vm',
            id_vm=id_vm,
            id_drive=id_drive,
            size_mb=self.size_mb
        )

    def get_acao_mover_disco(self, id_vm, id_disco):
        return Action(
            'mover_disco_vm',
            id_vm=id_vm,
            id_disco=id_disco,
            path=self.path
        )

    def get_acao_converter_disco(self, id_vm, id_drive):
        return Action(
            'converter_disco_vm',
            id_vm=id_vm,
            id_drive=id_drive,
            size_type=self.get_tamanho_tipo_create()
        )

    def get_acoes_diferenca_disco(self, disco_remoto, id_vm, vm_name):
        actions = []

        # Alteração de tipo ou redução de disco exige a recriação
        if ((self.bus_type != disco_remoto.bus_type) or
                (self.size_mb < disco_remoto.size_mb)):
            actions.append(disco_remoto.get_acao_excluir_disco(id_vm))
            actions.append(self.get_acao_criar_disco(vm_name))
        else:
            # Tipo de tamanho alterado: converter disco
            if self.size_type != disco_remoto.size_type:
                actions.append(self.get_acao_converter_disco(
                    id_vm, disco_remoto.get_id_drive()))

            # Tamanho alterado: expansão
            if self.size_mb > disco_remoto.size_mb:
                actions.append(self.get_acao_expandir_disco(
                    id_vm, disco_remoto.get_id_drive()))

            # Caminho alterado: mover disco
            if self.path and self.path != disco_remoto.path:
                actions.append(self.get_acao_mover_disco(
                    id_vm, disco_remoto.get_id_disco()))

        return actions

    def __hash__(self):
        return hash(self.file)

    def __eq__(self, other):
        return isinstance(other, VMDisk) and (self.bus_type == other.bus_type
                                              and self.file == other.file
                                              and self.size_mb == other.size_mb
                                              and self.size_type == other.size_type
                                              and self.path == other.path)

    def __repr__(self):
        return f'''
                bus_type: {self.bus_type}
                file: {self.file}
                size_mb: {self.size_mb}
                size_type: {self.size_type}
                path: {self.path}
                id_drive: {self.__id_drive}
                id_disco: {self.__id_disco}
                bus: {self.__bus}
                lun: {self.__lun}
                '''

    def to_dict(self):
        return {
            'bus_type': self.bus_type.value,
            'file': self.file,
            'size_mb': self.size_mb,
            'size_type': self.size_type.value,
            'path': self.path,
            'id_drive': self.__id_drive,
            'id_disco': self.__id_disco,
            'bus': self.__bus,
            'lun': self.__lun
        }
