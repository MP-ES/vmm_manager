"""
Classe de apoio e geração de dados para os testes
"""
from faker import Faker


class DadosTeste():
    def __init__(self):
        self.__faker = Faker()
        self.__nomes_unicos = []

    def get_nome_unico(self):
        nome_vm = self.get_random_word().upper()
        while nome_vm in self.__nomes_unicos:
            nome_vm = self.get_random_word().upper()

        self.__nomes_unicos.append(nome_vm)
        return nome_vm

    def get_random_word(self):
        word = self.__faker.format('word')
        while len(word) < 3:
            word = self.__faker.format('word')
        return word
