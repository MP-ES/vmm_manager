"""
Representação de uma máquina virtual
"""
from vmm_manager.scvmm.enums import VMStatusEnum
from vmm_manager.entidade.vm_ansible import VMAnsible
from vmm_manager.entidade.acao import Acao
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
        id_vmm=None,
        nested_virtualization=False,
        dynamic_memory=True,
        status=VMStatusEnum.EM_EXECUCAO,
        no_regiao=None
    ):
        self.name = name
        self.description = description if not description is None else ''
        self.image = image
        self.region = region
        self.cpu = cpu
        self.memory = memory
        self.networks = networks
        self.id_vmm = id_vmm
        self.status = status
        self.no_regiao = no_regiao
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
                    f"Grupo ansible '{group}' "
                    f"referenciado mais de uma vez para a VM '{self.name}'.")

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
                plano_execucao.acoes.append(
                    vm_remota.additional_disks[nome_disco].get_acao_excluir_disco(
                        vm_remota.id_vmm))

        # verificando discos atuais
        for nome_disco, data_disco in self.additional_disks.items():
            # discos a criar
            if not vm_remota or not nome_disco in vm_remota.additional_disks:
                plano_execucao.acoes.append(
                    data_disco.get_acao_criar_disco(self.name))
            else:
                # discos a alterar
                plano_execucao.acoes.extend(
                    data_disco.get_acoes_diferenca_disco(
                        vm_remota.additional_disks[nome_disco], vm_remota.id_vmm, self.name))

    def add_acoes_diferenca_regiao(
        self,
        vm_remota,
        plano_execucao,
        inv_remoto
    ):
        if self.region == SCRegion.REGIAO_PADRAO:
            return

        if (not vm_remota
            or (self.region != vm_remota.region or
                inv_remoto.get_nome_no_regiao(self.region) != vm_remota.no_regiao)):
            plano_execucao.acoes.append(self.get_acao_mover_vm_regiao(
                inv_remoto.get_id_no_regiao(self.region)))

    def add_acoes_virtualizacao_aninhada(self, vm_remota,
                                         plano_execucao):
        if ((not vm_remota and self.nested_virtualization)
                or (vm_remota and vm_remota.nested_virtualization != self.nested_virtualization)):
            plano_execucao.acoes.append(
                self.get_acao_atualizar_virtualizacao_aninhada())

    def add_acoes_memoria_dinamica(self, vm_remota,
                                   plano_execucao):
        if (vm_remota and vm_remota.dynamic_memory != self.dynamic_memory):
            plano_execucao.acoes.append(
                self.get_acao_atualizar_memoria_dinamica())

    def add_acoes_diferenca_vm(self, vm_remota, plano_execucao):
        # alteração da image é irreversível
        if self.image != vm_remota.image:
            plano_execucao.acoes.append(vm_remota.get_acao_excluir_vm())
            plano_execucao.acoes.append(self.get_acao_criar_vm())
            return

        # Alteração de network é possível recuperar TODO #18
        if self.networks != vm_remota.networks:
            plano_execucao.acoes.append(vm_remota.get_acao_excluir_vm())
            plano_execucao.acoes.append(self.get_acao_criar_vm())
            return

        # alteração de descrição, cpu ou ram
        if (self.description != vm_remota.description
                or self.cpu != vm_remota.cpu
                or self.memory != vm_remota.memory):
            plano_execucao.acoes.append(
                self.get_acao_atualizar_vm(vm_remota.id_vmm))

    def get_qtde_rede_principal(self):
        return sum(1 for network in self.networks if network.default)

    def get_rede_principal(self):
        return next((network.name for network in self.networks if network.default), None)

    def get_acao_criar_vm(self):
        return Acao(
            Acao.ACAO_CRIAR_VM,
            nome_vm=self.name,
            description=self.description,
            image=self.image,
            region=self.region,
            cpu=self.cpu,
            memory=self.memory,
            dynamic_memory=self.dynamic_memory,
            networks=[network.name for network in self.networks],
            rede_principal=self.get_rede_principal()
        )

    def get_acao_excluir_vm(self):
        return Acao(
            Acao.ACAO_EXCLUIR_VM,
            id_vm=self.id_vmm
        )

    def get_acao_mover_vm_regiao(self, id_no_regiao):
        return Acao(
            'mover_vm_regiao',
            nome_vm=self.name,
            id_no_regiao=id_no_regiao,
            region=self.region
        )

    def get_acao_atualizar_virtualizacao_aninhada(self):
        return Acao(
            'atualizar_virtualizacao_aninhada',
            nome_vm=self.name,
            nested_virtualization=self.nested_virtualization
        )

    def get_acao_atualizar_memoria_dinamica(self):
        return Acao(
            'atualizar_memoria_dinamica',
            nome_vm=self.name,
            dynamic_memory=self.dynamic_memory
        )

    def get_acao_atualizar_vm(self, id_vm_remota):
        return Acao(
            'atualizar_vm',
            id_vm=id_vm_remota,
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
                id_vmm: {self.id_vmm}
                status: {self.status}
                no_regiao: {self.no_regiao}
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
            'id_vmm': self.id_vmm,
            'status': self.status.value,
            'no_regiao': self.no_regiao,
            'ansible': [data_ansible.to_dict()
                        for data_ansible in self.dados_ansible.values()]
        }

        if self.to_json_dados_completos:
            dict_objeto['additional_disks'] = [data_disco.to_dict()
                                               for data_disco in self.additional_disks.values()]

        return dict_objeto
