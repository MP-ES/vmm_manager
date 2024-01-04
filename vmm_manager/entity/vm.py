"""
VM entity.
"""
from vmm_manager.entity.action import Action
from vmm_manager.entity.vm_ansible import VMAnsible
from vmm_manager.scvmm.enums import VMStatusEnum
from vmm_manager.scvmm.scregion import SCRegion


class VM:
    def __init__(
        self,
        name,
        description,
        image,
        region,
        cpu,
        memory,
        networks,
        vmm_id=None,
        nested_virtualization=False,
        dynamic_memory=True,
        status=VMStatusEnum.RUNNING,
        region_host=None
    ):
        self.name = name
        self.description = description if description is not None else ''
        self.image = image
        self.region = region
        self.cpu = cpu
        self.memory = memory
        self.networks = networks
        self.vmm_id = vmm_id
        self.status = status
        self.region_host = region_host
        self.nested_virtualization = nested_virtualization
        self.dynamic_memory = dynamic_memory

        self.dados_ansible = {}
        self.additional_disks = {}
        self.to_json_dados_completos = True

    def extrair_dados_ansible_dict(self, dict_ansible):
        for item in dict_ansible or {}:
            group = item.get('group')

            if group in self.dados_ansible:
                raise ValueError(
                    f"Ansible group '{group}' "
                    f"already exists in VM '{self.name}'.")

            ansible_grupo = VMAnsible(group)
            ansible_grupo.extrair_dados_vars_dict(
                item.get('vars'), self.name)

            self.dados_ansible[group] = ansible_grupo

    def add_discos_adicionais(self, additional_disks):
        for additional_disk in additional_disks:
            self.additional_disks[additional_disk.file] = additional_disk

    def add_acoes_diferenca_discos_adicionais(self, vm_remota, plano_execucao):
        # discos a excluir
        if vm_remota:
            discos_excluir = [
                nome_disco_remoto for nome_disco_remoto in vm_remota.additional_disks
                if nome_disco_remoto not in self.additional_disks
            ]
            for nome_disco in discos_excluir:
                plano_execucao.actions.append(
                    vm_remota.additional_disks[nome_disco].get_acao_excluir_disco(
                        vm_remota.vmm_id))

        # verificando discos atuais
        for nome_disco, data_disco in self.additional_disks.items():
            # discos a criar
            if not vm_remota or nome_disco not in vm_remota.additional_disks:
                plano_execucao.actions.append(
                    data_disco.get_acao_criar_disco(self.name))
            else:
                # discos a alterar
                plano_execucao.actions.extend(
                    data_disco.get_acoes_diferenca_disco(
                        vm_remota.additional_disks[nome_disco], vm_remota.vmm_id, self.name))

    def add_acoes_diferenca_regiao(
        self,
        vm_remota,
        plano_execucao,
        inv_remoto
    ):
        if self.region == SCRegion.REGION_DEFAULT:
            return

        if (not vm_remota
            or (self.region != vm_remota.region or
                inv_remoto.get_nome_no_regiao(self.region) != vm_remota.region_host)):
            plano_execucao.actions.append(self.get_acao_mover_vm_regiao(
                inv_remoto.get_id_no_regiao(self.region)))

    def add_acoes_virtualizacao_aninhada(self, vm_remota,
                                         plano_execucao):
        if ((not vm_remota and self.nested_virtualization)
                or (vm_remota and vm_remota.nested_virtualization != self.nested_virtualization)):
            plano_execucao.actions.append(
                self.get_acao_atualizar_virtualizacao_aninhada())

    def add_acoes_memoria_dinamica(self, vm_remota,
                                   plano_execucao):
        if (vm_remota and vm_remota.dynamic_memory != self.dynamic_memory):
            plano_execucao.actions.append(
                self.get_acao_atualizar_memoria_dinamica())

    def add_acoes_diferenca_vm(self, vm_remota, plano_execucao):
        # alteração da image é irreversível
        if self.image != vm_remota.image:
            plano_execucao.actions.append(vm_remota.get_acao_excluir_vm())
            plano_execucao.actions.append(self.get_acao_criar_vm())
            return

        # Alteração de network é possível recuperar TODO #18
        if self.networks != vm_remota.networks:
            plano_execucao.actions.append(vm_remota.get_acao_excluir_vm())
            plano_execucao.actions.append(self.get_acao_criar_vm())
            return

        # alteração de descrição, cpu ou ram
        if (self.description != vm_remota.description
                or self.cpu != vm_remota.cpu
                or self.memory != vm_remota.memory):
            plano_execucao.actions.append(
                self.get_acao_atualizar_vm(vm_remota.vmm_id))

    def get_qtde_rede_principal(self):
        return sum(1 for network in self.networks if network.default)

    def get_rede_principal(self):
        return next((network.name for network in self.networks if network.default), None)

    def get_acao_criar_vm(self):
        return Action(
            Action.ACAO_CRIAR_VM,
            vm_name=self.name,
            description=self.description,
            image=self.image,
            region=self.region,
            cpu=self.cpu,
            memory=self.memory,
            dynamic_memory=self.dynamic_memory,
            networks=[network.name for network in self.networks],
            network_default=self.get_rede_principal()
        )

    def get_acao_excluir_vm(self):
        return Action(
            Action.ACAO_EXCLUIR_VM,
            vm_id=self.vmm_id
        )

    def get_acao_mover_vm_regiao(self, region_host_id):
        return Action(
            'move_vm_region',
            vm_name=self.name,
            region_host_id=region_host_id,
            region=self.region
        )

    def get_acao_atualizar_virtualizacao_aninhada(self):
        return Action(
            'update_nested_virtualization',
            vm_name=self.name,
            nested_virtualization=self.nested_virtualization
        )

    def get_acao_atualizar_memoria_dinamica(self):
        return Action(
            'update_dynamic_memory',
            vm_name=self.name,
            dynamic_memory=self.dynamic_memory
        )

    def get_acao_atualizar_vm(self, id_vm_remota):
        return Action(
            'update_vm',
            vm_id=id_vm_remota,
            description=self.description,
            cpu=self.cpu,
            memory=self.memory
        )

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, VM) and (self.name == other.name
                                          and self.image == other.image
                                          and self.region == other.region
                                          and self.cpu == other.cpu
                                          and self.memory == other.memory
                                          # pylint: disable=line-too-long
                                          and self.nested_virtualization == other.nested_virtualization
                                          and self.dynamic_memory == other.dynamic_memory
                                          and self.networks == other.networks
                                          and self.status == other.status)

    def __repr__(self):
        return f'''
                name: {self.name}
                description: {self.description}
                image: {self.image}
                region: {self.region}
                cpu: {self.cpu}
                memory: {self.memory}
                networks: {self.networks}
                vmm_id: {self.vmm_id}
                status: {self.status}
                region_host: {self.region_host}
                ansible: {self.dados_ansible}
                additional_disks: {self.additional_disks}
                '''

    def to_dict(self):
        dict_objeto = {
            'name': self.name,
            'description': self.description,
            'image': self.image,
            'region': self.region,
            'cpu': self.cpu,
            'memory': self.memory,
            'networks': [network.to_dict() for network in self.networks],
            'vmm_id': self.vmm_id,
            'status': self.status.value,
            'region_host': self.region_host,
            'ansible': [data_ansible.to_dict()
                        for data_ansible in self.dados_ansible.values()]
        }

        if self.to_json_dados_completos:
            dict_objeto['additional_disks'] = [data_disco.to_dict()
                                               for data_disco in self.additional_disks.values()]

        return dict_objeto
