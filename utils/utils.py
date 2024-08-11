import random


def random_list_elem(list):
    list_len = len(list) - 1
    rand_num = random.randint(0, list_len)
    return rand_num


def word_conjugate(number):
    args = ['заявка', 'заявки', 'заявок']
    int_num = int(number)
    last_digit = int_num % 10
    last_two_digit = int_num % 100  # для проверки 11...14
    if last_digit == 1 and last_two_digit != 11:
        return f'{args[0]}'  # заявка
    if 1 < last_digit < 5 and last_two_digit not in range(11, 15):
        return f'{args[1]}'  # заявки
    return f'{args[2]}'  # заявок
