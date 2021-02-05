#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

class States(Enum):
    start = 0  # Начало нового диалога
    end = -1  # Отказ или конец
    name = -2  # имя
    surname = -3  # фамилия
    date = -4  # дата рождения
    opt_q1 = -5  # начало списка вопросов с опциональными пропусками
    opt_q2 = -6
    opt_q3 = -7
    opt_q4 = -8
    opt_q5 = -9
    opt_q6 = -10
    opt_q7 = -11
    opt_q8 = -12
    opt_q9 = -13
    id = -14