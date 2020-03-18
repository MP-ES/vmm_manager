"""
Módulo relacionado ao gerenciamento do inventário
"""
import os
import json
import yamale
from app.comando import Comando
from app.util import CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM, CAMPO_REGIAO
from app.scvmm import VMStatusEnum
from app.plano_execucao import PlanoExecucao, Acao


class ParserLocal:
    REGIAO_PADRAO = 'default'
    __ARQUIVO_SCHEMA = 'schema.yaml'
    __YAML_PARSER = 'ruamel'

    @staticmethod
    def __get_schema_yaml():
        return yamale.make_schema(
            ParserLocal.__ARQUIVO_SCHEMA,
            parser=ParserLocal.__YAML_PARSER)

    def __init__(self, arquivo_inventario):
        self.__arquivo_inventario = arquivo_inventario
        self.__inventario = None

    def __validar_arquivo_yaml(self):
        if not os.path.isfile(self.__arquivo_inventario):
            raise ValueError('Arquivo de inventário não encontrado.')
        if os.stat(self.__arquivo_inventario).st_size == 0:
            raise ValueError('Arquivo de inventário vazio.')

    def __validar_inventario_servidor(self, servidor_acesso):
        imagens = set()
        redes = set()
        regioes = set()
        for maquina_virtual in self.__inventario.vms.values():
            if maquina_virtual.imagem is None:
                raise ValueError(
                    'Imagem da VM {} não definida.'.format(maquina_virtual.nome))
            imagens.add(maquina_virtual.imagem)

            if maquina_virtual.regiao != ParserLocal.REGIAO_PADRAO:
                regioes.add(maquina_virtual.regiao)

            if maquina_virtual.qtde_cpu is None:
                raise ValueError(
                    'Quantidade de CPUs da VM {} não definida.'.format(maquina_virtual.nome))

            if maquina_virtual.qtde_ram_mb is None:
                raise ValueError(
                    'Quantidade de memória da VM {} não definida.'.format(maquina_virtual.nome))

            if maquina_virtual.redes is None:
                raise ValueError(
                    'Redes da VM {} não definida.'.format(maquina_virtual.nome))
            redes.update([rede['nome'] for rede in maquina_virtual.redes])

        cmd = Comando('validar_inventario', imagens=imagens,
                      nuvem=self.__inventario.nuvem,
                      redes=redes,
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      qtde_minima_regioes=len(regioes))
        _, msg = cmd.executar(servidor_acesso)
        if msg:
            raise ValueError(msg)

    def __montar_inventario(self, dados_inventario):
        nomes_vm = []
        self.__inventario = Inventario(
            dados_inventario['agrupamento'], dados_inventario['nuvem'])

        for maquina_virtual in dados_inventario['vms']:
            nome_vm = maquina_virtual.get('nome')
            if nome_vm in nomes_vm:
                raise ValueError(
                    'VM {} referenciada mais de uma vez no inventário.'.format(nome_vm))
            nomes_vm.append(nome_vm)

            self.__inventario.vms[nome_vm] = VM(
                nome_vm,
                maquina_virtual.get('descricao'),
                maquina_virtual.get(
                    'imagem', dados_inventario.get('imagem_padrao', None)),
                maquina_virtual.get('regiao', ParserLocal.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', dados_inventario.get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', dados_inventario.get('qtde_ram_mb_padrao', None)),
                maquina_virtual.get(
                    'redes', dados_inventario.get('redes_padrao', None))
            )

    def __carregar_yaml(self):
        return yamale.make_data(self.__arquivo_inventario,
                                parser=ParserLocal.__YAML_PARSER)

    def get_inventario(self, servidor_acesso):
        if not self.__inventario:
            try:
                self.__validar_arquivo_yaml()
                dados_yaml = self.__carregar_yaml()
                dados_inventario = yamale.validate(ParserLocal.__get_schema_yaml(),
                                                   dados_yaml, strict=True)
                self.__montar_inventario(dados_inventario[0][0])
                self.__validar_inventario_servidor(servidor_acesso)
            except (SyntaxError, ValueError) as ex:
                return False, str(ex)

        return True, self.__inventario


class ParserRemoto:
    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.__inventario = None

    def __get_vms_servidor(self, servidor_acesso):
        cmd = Comando('obter_vms_agrupamento',
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                      campo_id=CAMPO_ID[0],
                      campo_imagem=CAMPO_IMAGEM[0],
                      campo_regiao=CAMPO_REGIAO[0],
                      agrupamento=self.agrupamento, nuvem=self.nuvem)
        status, vms = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(
                "Erro ao recuperar VM's do agrupamento: {}".format(vms))
        return vms

    def __montar_inventario(self, servidor_acesso):
        self.__inventario = Inventario(self.agrupamento, self.nuvem)
        vms_servidor = json.loads(
            self.__get_vms_servidor(servidor_acesso) or '{}')
        for maquina_virtual in vms_servidor:
            self.__inventario.vms[maquina_virtual.get('Nome')] = VM(
                maquina_virtual.get('Nome'),
                maquina_virtual.get('Descricao'),
                maquina_virtual.get('Imagem'),
                maquina_virtual.get('Regiao'),
                maquina_virtual.get('QtdeCpu'),
                maquina_virtual.get('QtdeRam'),
                maquina_virtual.get('Redes'),
                maquina_virtual.get('ID'),
                VMStatusEnum(maquina_virtual.get('Status')),
                maquina_virtual.get('NoRegiao'),
            )

    def get_inventario(self, servidor_acesso):
        if not self.__inventario:
            try:
                self.__montar_inventario(servidor_acesso)
            # pylint: disable=broad-except
            except Exception as ex:
                return False, str(ex)

        return True, self.__inventario


class Inventario:
    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.vms = {}

    def calcular_plano_execucao(self, inventario_remoto):
        if (self.agrupamento != inventario_remoto.agrupamento
                or self.nuvem != inventario_remoto.nuvem):
            return False, 'Não é possível calcular o plano de execução \
                para inventários de agrupamento ou nuvem distintos.'

        plano_execucao = PlanoExecucao(self.agrupamento, self.nuvem)

        self.__add_acoes_criar_vms(inventario_remoto, plano_execucao)
        self.__add_acoes_execucao_excluir_vms(
            inventario_remoto, plano_execucao)

        return True, plano_execucao

    def gerar_plano_exclusao(self):
        plano_execucao = PlanoExecucao(self.agrupamento, self.nuvem)

        for maquina_virtual in self.vms.values():
            plano_execucao.acoes.append(
                Acao('excluir_vm',
                     id_vmm=maquina_virtual.id_vmm
                     )
            )

        return plano_execucao

    def is_vazio(self):
        return not self.vms

    def __add_acoes_criar_vms(self, inventario_remoto, plano_execucao):
        vms_inserir = [
            nome_vm_local for nome_vm_local in self.vms
            if nome_vm_local not in inventario_remoto.vms
        ]
        for nome_vm in vms_inserir:
            plano_execucao.acoes.append(
                Acao('criar_vm',
                     nome=self.vms[nome_vm].nome,
                     descricao=self.vms[nome_vm].descricao,
                     imagem=self.vms[nome_vm].imagem,
                     regiao=self.vms[nome_vm].regiao,
                     qtde_cpu=self.vms[nome_vm].qtde_cpu,
                     qtde_ram_mb=self.vms[nome_vm].qtde_ram_mb,
                     redes=[rede['nome'] for rede in self.vms[nome_vm].redes]
                     )
            )

    def __add_acoes_execucao_excluir_vms(self, inventario_remoto, plano_execucao):
        vms_excluir = [
            nome_vm_remoto for nome_vm_remoto in inventario_remoto.vms
            if nome_vm_remoto not in self.vms
        ]
        for nome_vm in vms_excluir:
            plano_execucao.acoes.append(
                Acao('excluir_vm',
                     id_vmm=inventario_remoto.vms[nome_vm].id_vmm
                     )
            )

    def __eq__(self, other):
        return isinstance(other, Inventario) and (self.agrupamento == other.agrupamento
                                                  and self.nuvem == other.nuvem
                                                  and self.vms == other.vms)

    def __str__(self):
        return '''
            agrupamento: {}
            nuvem: {}
            vms: {}
            '''.format(self.agrupamento,
                       self.nuvem,
                       self.vms)


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
