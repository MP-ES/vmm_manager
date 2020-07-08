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
                    "Grupo ansible '{}' referenciado mais de uma vez para a VM '{}'.".format(
                        grupo, self.nome))

            ansible_grupo = VMAnsible(grupo)
            ansible_grupo.extrair_dados_vars_dict(
                item.get('vars'), self.nome)

            self.dados_ansible[grupo] = ansible_grupo

    def extrair_discos_adicionais_dict(self, dict_discos_adicionais):
        for item in dict_discos_adicionais or {}:
            nome_arquivo = item.get('nome_arquivo')

            if nome_arquivo in self.discos_adicionais:
                raise ValueError(
                    "Disco '{}' referenciado mais de uma vez para a VM '{}'.".format(
                        nome_arquivo, self.nome))

            disco_adicional = VMDisco(
                SCDiskBusType(item.get('tipo')),
                item.get('nome_arquivo'),
                item.get('tamanho_mb'),
                SCDiskSizeType(item.get('tamanho_tipo')),
                item.get('caminho_arquivo'))

            self.discos_adicionais[nome_arquivo] = disco_adicional

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
        return '''
                nome: {}
                descricao: {}
                imagem: {}
                regiao: {}
                qtde_cpu: {}
                qtde_ram_mb: {}
                redes: {}
                id_vmm: {}
                status: {}
                no_regiao: {}
                ansible: {}
                discos_adicionais: {}
                '''.format(self.nome,
                           self.descricao,
                           self.imagem,
                           self.regiao,
                           self.qtde_cpu,
                           self.qtde_ram_mb,
                           self.redes,
                           self.id_vmm,
                           self.status,
                           self.no_regiao,
                           self.dados_ansible,
                           self.discos_adicionais)

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
