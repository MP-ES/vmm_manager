"""
Representação de uma máquina virtual
"""
from vmm_manager.scvmm.enums import VMStatusEnum


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
                '''.format(self.nome,
                           self.descricao,
                           self.imagem,
                           self.regiao,
                           self.qtde_cpu,
                           self.qtde_ram_mb,
                           self.redes,
                           self.id_vmm,
                           self.status,
                           self.no_regiao)
