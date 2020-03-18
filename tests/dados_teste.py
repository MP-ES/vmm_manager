"""
Classe de apoio e geração de dados para os testes
"""
from faker import Faker


class DadosTeste():
    def __init__(self):
        self.__faker = Faker()
        self.__nomes_vm = []

    def get_nome_vm(self):
        nome_vm = self.get_random_word()
        while nome_vm in self.__nomes_vm:
            nome_vm = self.get_random_word()

        self.__nomes_vm.append(nome_vm)
        return nome_vm

    def get_random_word(self):
        word = self.__faker.format('word')
        while len(word) < 3:
            word = self.__faker.format('word')
        return word
