"""
Testes do ParserLocal (casos que precisam dar erro)
"""
from unittest import mock
from random import randrange, randint, choice
import re
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.parser.parser_local import ParserLocal
from tests.base import Base
from tests.dados_teste import DadosTeste


class TestParserLocalValidacao(Base):

    def test_parser_inventario_vazio(self, tmpdir, servidor_acesso):
        inventory_file = tmpdir.join('inventario_vazio.yaml')
        inventory_file.write('')

        parser_local = ParserLocal(inventory_file.strpath)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'Arquivo de inventário vazio.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_sem_imagem(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Imagem da VM {inventario[0][0]['vms'][0]['nome']} não definida."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_nome_invalido(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        qtde_vms = randrange(1, Base.VMS_POR_TESTE_MAX)
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_random_nome_vm_incorreto()
             } for _ in range(qtde_vms)]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert qtde_vms == sum(1 for _ in re.finditer(
            re.escape('is not a caracteres alfanuméricos (máx 15)'), msg))

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_sem_rede(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(Base.CPU_MIN, Base.CPU_MAX),
             'qtde_ram_mb_padrao': randint(Base.RAM_MIN, Base.RAM_MAX),
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"VM {inventario[0][0]['vms'][0]['nome']}" \
            ' deve ter exatamente uma rede principal.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_sem_rede_principal(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(Base.CPU_MIN, Base.CPU_MAX),
             'qtde_ram_mb_padrao': randint(Base.RAM_MIN, Base.RAM_MAX),
             'redes_padrao': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"VM {inventario[0][0]['vms'][0]['nome']}" \
            ' deve ter exatamente uma rede principal.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_rede_duplicada(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_rede = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(Base.CPU_MIN, Base.CPU_MAX),
             'qtde_ram_mb_padrao': randint(Base.RAM_MIN, Base.RAM_MAX),
             'redes_padrao': [{
                 'nome': nome_rede,
                 'principal': num_iter == 0,
             } for num_iter in range(randrange(2, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Rede '{nome_rede}' referenciada mais de uma vez " \
            f"para a VM '{inventario[0][0]['vms'][0]['nome']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_com_regiao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(Base.CPU_MIN, Base.CPU_MAX),
             'qtde_ram_mb_padrao': randint(Base.RAM_MIN, Base.RAM_MAX),
             'redes_padrao': [{
                 'nome': dados_teste.get_nome_unico(),
                 'principal': num_iter == 0,
             } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'regiao': DadosTeste.get_regiao_vm_por_iteracao(num_iter)
             } for num_iter in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, _ = parser_local.get_inventario(servidor_acesso)

        assert status is True

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_sem_grupo(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': '',
                         'vars': [
                             {
                                 'nome': dados_teste.get_random_word(),
                                 'valor': dados_teste.get_random_word()
                             }
                         ]
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert "vms.0.ansible.0.grupo: '' is not a caracteres alfabéticos." in msg

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_grupo_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_grupo = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': nome_grupo,
                         'vars': [
                             {
                                 'nome': dados_teste.get_random_word(),
                                 'valor': dados_teste.get_random_word()
                             }
                         ]
                     },
                     {
                         'grupo': nome_grupo
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Grupo ansible '{nome_grupo}' referenciado mais de uma vez " \
            f"para a VM '{inventario[0][0]['vms'][0]['nome']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_grupo_var_duplicada(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_grupo = dados_teste.get_nome_unico()
        nome_var = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': nome_grupo,
                         'vars': [
                             {
                                 'nome': nome_var,
                                 'valor': dados_teste.get_random_word()
                             },
                             {
                                 'nome': nome_var,
                                 'valor': dados_teste.get_random_word()
                             }
                         ]
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Variável '{nome_var}' do grupo ansible '{nome_grupo}' " \
            f"referenciada mais de uma vez na VM '{inventario[0][0]['vms'][0]['nome']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_var_invalida(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': dados_teste.get_random_word(),
                         'vars': [
                             {
                                 'nome': ''
                             }
                         ]
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert "vms.0.ansible.0.vars.0.nome: '' is not a caracteres alfabéticos" in msg
        assert 'vms.0.ansible.0.vars.0.valor: Required field missing' in msg

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_disco_adicional_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        arquivo = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'discos_adicionais': [
                     {
                         'arquivo': arquivo,
                         'tipo': choice([enum.value for enum in SCDiskBusType]),
                         'tamanho_mb': randint(Base.TAMANHO_DISCO_MIN, Base.TAMANHO_DISCO_MAX),
                         'tamanho_tipo': choice([enum.value for enum in SCDiskSizeType]),
                     },
                     {
                         'arquivo': arquivo,
                         'tipo': choice([enum.value for enum in SCDiskBusType]),
                         'tamanho_mb': randint(Base.TAMANHO_DISCO_MIN, Base.TAMANHO_DISCO_MAX),
                         'tamanho_tipo': choice([enum.value for enum in SCDiskSizeType]),
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Disco '{arquivo}' referenciado mais de uma vez " \
            f"para a VM '{inventario[0][0]['vms'][0]['nome']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_nome_vm_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_vm = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(Base.CPU_MIN, Base.CPU_MAX),
             'qtde_ram_mb_padrao': randint(Base.RAM_MIN, Base.RAM_MAX),
             'redes_padrao': [{
                 'nome': dados_teste.get_random_word()
             } for _ in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'nome': nome_vm
             } for _ in range(randrange(2, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"VM {inventario[0][0]['vms'][0]['nome']}" \
            ' referenciada mais de uma vez no inventário.'
