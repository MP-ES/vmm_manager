"""
Módulo relacionado à preparação de comandos para execução no servidor de acesso
"""
import os
import sys

from jinja2 import Environment, FileSystemLoader, exceptions


class Comando:
    __TEMPLATES_DIR = '../includes/ps_templates'
    __TEMPLATES_EXTENSAO = '.j2'

    def __init__(self, comando, descricao=None, **kwargs):
        try:
            self.comando = comando
            self.descricao = descricao if descricao else self.comando
            self.args = kwargs
            j2_env = Environment(
                loader=FileSystemLoader(os.path.join(
                    os.path.dirname(__file__), Comando.__TEMPLATES_DIR)),
                trim_blocks=True)
            self.template = j2_env.get_template(
                self.comando + Comando.__TEMPLATES_EXTENSAO)
        except exceptions.TemplateNotFound as ex:
            print(
                f"Template '{ex}' não encontrado para o comando '{self.comando}'.")
            sys.exit(1)

    def imprimir(self):
        print('\n' + self.template.render(self.args) + '\n')

    def executar(self, servidor_acesso):
        conteudo_script = self.template.render(self.args)
        return servidor_acesso.executar_script(
            self.comando, conteudo_script)
