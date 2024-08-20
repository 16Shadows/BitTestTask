from __future__ import annotations

from typing import Self, Callable
from collections.abc import Sequence

from modules.menu.static import StaticMenuEntry, MenuEntryBack
from modules.menu.core import MenuBase, MenuEntryBase, MenuHostBase
from modules.menu.input import converter_int, validator_int_range

import math

class PaginationMenu[T](MenuBase):
    '''
    Меню, отображающее список записей с поддержкой пагинации
    '''
    def __init__(self, items: Sequence[T],
                 entry_generator : Callable[[T], MenuEntryBase] | None = None,
                 text_generator : Callable[[T], str] | None = None) -> None:
        '''
        items: Sequence[T] -- список записей, которые необходимо отобразить.
        entry_generator : Callable[[T], MenuEntryBase] | None - генератор пункта меню для записи.
                                                                Если установлен, то записи отображаются в виде пунктов меню.
                                                                Несовместим с text_generator.
        text_generator : Callable[[T], str] | None - генератор текст для записи.
                                                     Если установлен, то записи отображаются в виде заголовка меню.
                                                     Несовместим с entry_generator.        
        '''

        if entry_generator is not None and text_generator is not None:
            raise ValueError('PaginationMenu cannot have both entry_generator and text_generator set')

        self._entry_generator = entry_generator
        self._text_generator = text_generator
        self._items = items
        self.__currentPage = 0
        self._pageSize = 10

    @MenuBase.text.getter
    def text(self: Self) -> str:
        items_len = len(self._items)
        if items_len < 1:
            return 'Список пуст.'
        
        if self._text_generator is None:
            return f'Страница {self._current_page + 1}/{ self._page_count }\nВсего записей: {items_len}'
        else:
            res = ''
            for item in self._items[self._current_page * self._pageSize:(self._current_page + 1) * self._pageSize]:
                res += self._text_generator(item) + '\n'
            res += f'Страница {self._current_page + 1}/{ self._page_count }\nВсего записей: {items_len}'
            return res

    @MenuBase.entries.getter
    def entries(self: Self) -> list[MenuEntryBase]:
        entries : list[MenuEntryBase] = []

        items_cnt = len(self._items)

        if items_cnt > 0:
            #Добавить опцию изменения размера страницы
            entries.append(StaticMenuEntry('Изменить размер страницы', self._change_page_size))

            #Добавить опцию перехода на следующую страницу, если не на последней странице
            if (self._current_page + 1) * self._pageSize < items_cnt:
                entries.append(StaticMenuEntry('Следующая страница', self._next_page))

            #Добавить опцию перехода на предыдущую страницу, если не на первой странице
            if self._current_page > 0:
                entries.append(StaticMenuEntry('Предыдущая страница', self._previous_page))

            #Добавить все записи текущей страницы как пункты меню
            if self._entry_generator is not None:
                for item in self._items[self._current_page * self._pageSize:(self._current_page + 1) * self._pageSize]:
                    entries.append(self._entry_generator(item))
                

        #Добавить опцию перехода к предыдущему меню
        entries.append(MenuEntryBack())

        return entries

    @property
    def _page_count(self: Self) -> int:
        '''Число страниц с текущими настройками'''
        return int(math.ceil(len(self._items) / self._pageSize))

    @property
    def _current_page(self: Self) -> int:
        '''Текущая страница, ограниченная числом страниц.'''
        self.__currentPage = min(self.__currentPage, self._page_count - 1)
        return self.__currentPage

    def _previous_page(self: Self, _: MenuHostBase) -> None:
        '''Перейти на предыдущую страницу, если не на первой странице.'''
        if (self._current_page > 0):
            self.__currentPage -= 1

    def _next_page(self: Self, _: MenuHostBase) -> None:
        '''Перейти на следующую страницу, если не на последней странице'''
        if self._current_page < self._page_count:
            self.__currentPage += 1

    def _change_page_size(self: Self, host:MenuHostBase) -> None:
        '''Изменить число записей на странице'''
        size = host.input('Введите желаемое число записей на странице (или нажмите Ctrl + C для отмены): ',
                           converter_int, lambda x: validator_int_range(x, 1),
                           'Количество записей на странице должно быть целым числом не меньше 1!')
        if size is None:
            return
        self._pageSize = size