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

    def set_parametros_extras_vmm(self, drive_id, disk_id, bus, lun):
        self.__id_drive = drive_id
        self.__id_disco = disk_id
        self.__bus = bus
        self.__lun = lun

    def get_id_disco(self):
        if not self.__id_disco:
            raise ValueError('Local disk does not have an ID.')

        return self.__id_disco

    def get_id_drive(self):
        if not self.__id_drive:
            raise ValueError('Local drive does not have an ID.')

        return self.__id_drive

    def get_tamanho_tipo_create(self):
        return self.size_type.name

    def get_acao_criar_disco(self, vm_name):
        return Action(
            'create_vm_disk',
            vm_name=vm_name,
            bus_type=self.bus_type.value,
            size_mb=self.size_mb,
            size_type=self.get_tamanho_tipo_create(),
            file=self.file,
            path=self.path
        )

    def get_acao_excluir_disco(self, vm_id):
        return Action(
            Action.ACAO_EXCLUIR_DISCO_VM,
            vm_id=vm_id,
            drive_id=self.get_id_drive()
        )

    def get_acao_expandir_disco(self, vm_id, drive_id):
        return Action(
            'expand_vm_disk',
            vm_id=vm_id,
            drive_id=drive_id,
            size_mb=self.size_mb
        )

    def get_acao_mover_disco(self, vm_id, disk_id):
        return Action(
            'mover_disco_vm',
            vm_id=vm_id,
            disk_id=disk_id,
            path=self.path
        )

    def get_acao_converter_disco(self, vm_id, drive_id):
        return Action(
            'convert_vm_disk',
            vm_id=vm_id,
            drive_id=drive_id,
            size_type=self.get_tamanho_tipo_create()
        )

    def get_acoes_diferenca_disco(self, disco_remoto, vm_id, vm_name):
        actions = []

        # Alteração de tipo ou redução de disco exige a recriação
        if ((self.bus_type != disco_remoto.bus_type) or
                (self.size_mb < disco_remoto.size_mb)):
            actions.append(disco_remoto.get_acao_excluir_disco(vm_id))
            actions.append(self.get_acao_criar_disco(vm_name))
        else:
            # Type de tamanho alterado: converter disco
            if self.size_type != disco_remoto.size_type:
                actions.append(self.get_acao_converter_disco(
                    vm_id, disco_remoto.get_id_drive()))

            # Tamanho alterado: expansão
            if self.size_mb > disco_remoto.size_mb:
                actions.append(self.get_acao_expandir_disco(
                    vm_id, disco_remoto.get_id_drive()))

            # Path alterado: mover disco
            if self.path and self.path != disco_remoto.path:
                actions.append(self.get_acao_mover_disco(
                    vm_id, disco_remoto.get_id_disco()))

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
                drive_id: {self.__id_drive}
                disk_id: {self.__id_disco}
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
            'drive_id': self.__id_drive,
            'disk_id': self.__id_disco,
            'bus': self.__bus,
            'lun': self.__lun
        }
