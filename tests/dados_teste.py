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

    @staticmethod
    def get_regiao_vm_por_iteracao(num_iter):
        return chr(ord('A') + num_iter)

    def __init__(self):
        self.__faker = Faker()
        self.__nomes_unicos = []

    def get_nome_unico(self):
        vm_name = self.get_random_word().upper()
        while vm_name in self.__nomes_unicos:
            vm_name = self.get_random_word().upper()

        self.__nomes_unicos.append(vm_name)
        return vm_name

    def get_random_word(self):
        word = self.__faker.format('word')
        while len(word) < 3:
            word = self.__faker.format('word')
        return word

    def get_random_nome_vm_incorreto(self):
        word = self.get_random_word()
        if choice([True, False]):
            word = word * 6
        else:
            word = word + '_-'
        return word
