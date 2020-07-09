"""
Representação de uma máquina virtual
"""
from vmm_manager.scvmm.enums import VMStatusEnum, SCDiskBusType, SCDiskSizeType
from vmm_manager.entidade.vm_ansible import VMAnsible
from vmm_manager.entidade.vm_disco import VMDisco


class VM:
    def __init__(self, nome, descricao,
                 imagem, regiao,
                 qtde_cpu, qtde_ram_mb, redes,
                 id_vmm=None,
                 status=VMStatusEnum.EM_EXECUCAO,
                 no_regiao=None):
        self.nome = nome
        self.descricao = descricao
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

    def extrair_discos_adicionais_dict(self, dict_discos_adicionais):
        for item in dict_discos_adicionais or {}:
            arquivo = item.get('arquivo')

            if arquivo in self.discos_adicionais:
                raise ValueError(
                    f"Disco '{arquivo}' referenciado mais de uma vez "
                    f"para a VM '{self.nome}'.")

            disco_adicional = VMDisco(
                SCDiskBusType(item.get('tipo')),
                item.get('arquivo'),
                item.get('tamanho_mb'),
                SCDiskSizeType(item.get('tamanho_tipo')),
                item.get('caminho'))

            self.discos_adicionais[arquivo] = disco_adicional

    def get_qtde_rede_principal(self):
        return sum([1 for rede in self.redes if rede.principal])

    def get_rede_principal(self):
        return next((rede.nome for rede in self.redes if rede.principal), None)

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
        return {
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
                        for dados_ansible in self.dados_ansible],
            'discos_adicionais': [self.discos_adicionais[disco_adicional].to_dict()
                                  for disco_adicional in self.discos_adicionais]
        }
