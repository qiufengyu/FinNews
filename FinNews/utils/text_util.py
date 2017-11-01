# -*- coding: utf-8 -*-
import re


def remove_multi_space(text):
    text = re.sub(r"\xa0", " ", text)
    return re.sub(r"\s{2,}", " ", text)


def remove_newline_character(text):
    return re.sub(r"\n", " ", text)
