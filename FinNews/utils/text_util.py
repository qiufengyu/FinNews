# -*- coding: utf-8 -*-
import re


def remove_multi_space(text):
    text = re.sub(r"\xa0", " ", text)
    return re.sub(r"\s{2,}", " ", text)


def remove_newline_character(text):
    return re.sub(r"\n", " ", text)



def get_code2name():
    dat = [line.strip().split(':') for line in open('./code2name.dat', 'r', encoding="utf-8").readlines()]
    res = {}
    for li in dat:
        if len(li) != 2:
            continue
        res[li[0].strip()] = (li[1]).strip()
    return res
