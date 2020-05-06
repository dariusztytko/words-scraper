#!/usr/bin/env python3
import sys
import unidecode


def get_words():
    for line in sys.stdin:
        yield line.strip()


def remove_accents(value):
    return unidecode.unidecode(value)


def remove_special_chars(value):
    for c in '~`!@#$%^&*()_+-=[]\\{}|;\':",./<>?':
        value = value.replace(c, '')
    return value


def convert_words():
    for word in get_words():
        converted_words = []
        multi_converted_word = word
        words = [word]
        for word_converter in [remove_accents, remove_special_chars]:
            converted_word = word_converter(word)
            multi_converted_word = word_converter(multi_converted_word)
            if converted_word and converted_word != word:
                words.append(converted_word)
                converted_words.append(converted_word)
        if (
            multi_converted_word
            and multi_converted_word != word
            and multi_converted_word not in converted_words
        ):
            words.append(multi_converted_word)
        print(*words, sep='\n')


def main():
    convert_words()


if __name__ == '__main__':
    main()
