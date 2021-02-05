"""
Representação de uma máquina virtual
"""
from vmm_manager.scvmm.enums import VMStatusEnum
from vmm_manager.entidade.vm_ansible import VMAnsible
from vmm_manager.entidade.acao import Acao
from vmm_manager.scvmm.scregion import SCRegion


class VM:
    def __init__(self, nome, descricao,
                 imagem, regiao,
                 qtde_cpu, qtde_ram_mb, redes,
                 id_vmm=None,
                 status=VMStatusEnum.EM_EXECUCAO,
                 no_regiao=None):
        self.nome = nome
        self.descricao = descricao if not descricao is None else ''
        self.imagem = imagem
        self.regiao = regiao
        self.qtde_cpu = qtde_cpu
        self.qtde_ram_mb = qtde_ram_mb
        self.redes = redes
        self.id_vmm = id_vmm
        self.status = status
        self.no_regiao = no_regiao

        self.dados_ansible = {}
        self.discos_adicionais = {}
        self.to_json_dados_completos = True

    def extrair_dados_ansible_dict(self, dict_ansible):
        for item in dict_ansible or {}:
            grupo = item.get('grupo')

            if grupo in self.dados_ansible:
                raise ValueError(
                    f"Grupo ansible '{grupo}' "
                    f"referenciado mais de uma vez para a VM '{self.nome}'.")

            ansible_grupo = VMAnsible(grupo)
            ansible_grupo.extrair_dados_vars_dict(
                item.get('vars'), self.nome)

            self.dados_ansible[grupo] = ansible_grupo

    def add_discos_adicionais(self, discos_adicionais):
        for disco_adicional in discos_adicionais:
            self.discos_adicionais[disco_adicional.arquivo] = disco_adicional

    def add_acoes_diferenca_discos_adicionais(self, vm_remota, plano_execucao):
        # discos a excluir
        if vm_remota:
            discos_excluir = [
                nome_disco_remoto for nome_disco_remoto in vm_remota.discos_adicionais
                if nome_disco_remoto not in self.discos_adicionais
            ]
            for nome_disco in discos_excluir:
                plano_execucao.acoes.append(
                    vm_remota.discos_adicionais[nome_disco].get_acao_excluir_disco(
                        vm_remota.id_vmm))

        # verificando discos atuais
        for nome_disco in self.discos_adicionais:
            # discos a criar
            if not vm_remota or not nome_disco in vm_remota.discos_adicionais:
                plano_execucao.acoes.append(
                    self.discos_adicionais[nome_disco].get_acao_criar_disco(self.nome))
            else:
                # discos a alterar
                plano_execucao.acoes.extend(
                    self.discos_adicionais[nome_disco].get_acoes_diferenca_disco(
                        vm_remota.discos_adicionais[nome_disco], vm_remota.id_vmm, self.nome))

    def add_acoes_diferenca_regiao(self, vm_remota,
                                   plano_execucao, inv_remoto):
        if (self.regiao != SCRegion.REGIAO_PADRAO
            and (not vm_remota
                 or (self.regiao != vm_remota.regiao or
                     inv_remoto.get_nome_no_regiao(self.regiao) != vm_remota.no_regiao))):
            plano_execucao.acoes.append(self.get_acao_mover_vm_regiao(
                inv_remoto.get_id_no_regiao(self.regiao)))

    def add_acoes_diferenca_vm(self, vm_remota, plano_execucao):
        # alteração da imagem é irreversível
        if self.imagem != vm_remota.imagem:
            plano_execucao.acoes.append(vm_remota.get_acao_excluir_vm())
            plano_execucao.acoes.append(self.get_acao_criar_vm())
            return

        # Alteração de rede é possível recuperar TODO #18
        if self.redes != vm_remota.redes:
            plano_execucao.acoes.append(vm_remota.get_acao_excluir_vm())
            plano_execucao.acoes.append(self.get_acao_criar_vm())
            return

        # alteração de descrição, cpu ou ram
        if (self.descricao != vm_remota.descricao
                or self.qtde_cpu != vm_remota.qtde_cpu
                or self.qtde_ram_mb != vm_remota.qtde_ram_mb):
            plano_execucao.acoes.append(
                self.get_acao_atualizar_vm(vm_remota.id_vmm))

    def get_qtde_rede_principal(self):
        return sum([1 for rede in self.redes if rede.principal])

    def get_rede_principal(self):
        return next((rede.nome for rede in self.redes if rede.principal), None)

    def get_acao_criar_vm(self):
        return Acao(Acao.ACAO_CRIAR_VM,
                    nome=self.nome,
                    descricao=self.descricao,
                    imagem=self.imagem,
                    regiao=self.regiao,
                    qtde_cpu=self.qtde_cpu,
                    qtde_ram_mb=self.qtde_ram_mb,
                    redes=[rede.nome for rede in self.redes],
                    rede_principal=self.get_rede_principal()
                    )

    def get_acao_excluir_vm(self):
        return Acao(Acao.ACAO_EXCLUIR_VM,
                    id_vmm=self.id_vmm)

    def get_acao_mover_vm_regiao(self, id_no_regiao):
        return Acao('mover_vm_regiao',
                    nome_vm=self.nome,
                    id_no_regiao=id_no_regiao,
                    regiao=self.regiao)

    def get_acao_atualizar_vm(self, id_vm_remota):
        return Acao('atualizar_vm',
                    id_vm=id_vm_remota,
                    descricao=self.descricao,
                    qtde_cpu=self.qtde_cpu,
                    qtde_ram_mb=self.qtde_ram_mb)

    def __hash__(self):
        return hash(self.nome)

    def __eq__(self, other):
        return isinstance(other, VM) and (self.nome == other.nome
                                          and self.imagem == other.imagem
                                          and self.regiao == other.regiao
                                          and self.qtde_cpu == other.qtde_cpu
                                          and self.qtde_ram_mb == other.qtde_ram_mb
                                          and self.redes == other.redes
                                          and self.status == other.status)

    def __repr__(self):
        return f'''
                nome: {self.nome}
                descricao: {self.descricao}
                imagem: {self.imagem}
                regiao: {self.regiao}
                qtde_cpu: {self.qtde_cpu}
                qtde_ram_mb: {self.qtde_ram_mb}
                redes: {self.redes}
                id_vmm: {self.id_vmm}
                status: {self.status}
                no_regiao: {self.no_regiao}
                ansible: {self.dados_ansible}
                discos_adicionais: {self.discos_adicionais}
                '''

    def to_dict(self):
        dict_objeto = {
            'nome': self.nome,
            'descricao': self.descricao,
            'imagem': self.imagem,
            'regiao': self.regiao,
            'qtde_cpu': self.qtde_cpu,
            'qtde_ram_mb': self.qtde_ram_mb,
            'redes': [rede.to_dict() for rede in self.redes],
            'id_vmm': self.id_vmm,
            'status': self.status.value,
            'no_regiao': self.no_regiao,
            'ansible': [self.dados_ansible[dados_ansible].to_dict()
                        for dados_ansible in self.dados_ansible]
        }

        if self.to_json_dados_completos:
            dict_objeto['discos_adicionais'] = [self.discos_adicionais[disco_adicional].to_dict()
                                                for disco_adicional in self.discos_adicionais]

        return dict_objeto
