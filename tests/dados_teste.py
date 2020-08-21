"""
Classe de apoio e geração de dados para os testes
"""
from random import choice, randint
from faker import Faker


class DadosTeste():

    @staticmethod
    def get_random_lista_com_excecao(lista, excecao):
        return choice([item for item in lista if item != excecao])

    @staticmethod
    def get_random_regiao_vm(qtde_regioes):
        return chr(ord('A') + randint(0, qtde_regioes - 1))

    @ staticmethod
    def get_random_string_com_excecao(excecao):
        faker = Faker()
        string_random = faker.format('word')
        while string_random == excecao:
            string_random = faker.format('word')

        return string_random

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
