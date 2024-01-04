"""
Módulo relacionado à preparação de comandos para execução no servidor de acesso
"""
import os
import sys

from jinja2 import Environment, FileSystemLoader, exceptions


class Command:
    __TEMPLATES_DIR = '../includes/ps_templates'
    __TEMPLATES_EXTENSION = '.j2'

    def __init__(self, command, description=None, **kwargs):
        try:
            self.command = command
            self.description = description if description else self.command
            self.args = kwargs
            j2_env = Environment(
                loader=FileSystemLoader(os.path.join(
                    os.path.dirname(__file__), Command.__TEMPLATES_DIR)),
                trim_blocks=True)
            self.template = j2_env.get_template(
                self.command + Command.__TEMPLATES_EXTENSION)
        except exceptions.TemplateNotFound as ex:
            print(
                f"Template '{ex}' not found for the command '{self.command}'.")
            sys.exit(1)

    def imprimir(self):
        print('\n' + self.template.render(self.args) + '\n')

    def executar(self, servidor_acesso):
        conteudo_script = self.template.render(self.args)
        return servidor_acesso.executar_script(
            self.command, conteudo_script)
