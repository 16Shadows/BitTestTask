from __future__ import annotations

from typing import Self, Callable
from collections.abc import Sequence
from .core import MenuBase, MenuEntryBase, MenuHostBase

class SimpleConsoleMenuHost(MenuHostBase):
    """Реализация MenuHost, выводящая пункты меню построчно в консоль и предлагающая пользователю ввести номер пункта."""
    def run(self: Self, enterAt: MenuBase | None = None) -> None:
        if enterAt is not None:
            self.menuStack.clear()
            self.push(enterAt)
        
        while len(self.menuStack) > 0:
            currentMenu : MenuBase = self.current()
            currentMenuEntries : Sequence[MenuEntryBase] = currentMenu.entries

            while True:
                print()
                print(currentMenu.text)
                for i in range(0, len(currentMenuEntries)):
                    print(i+1, ". ", currentMenuEntries[i].text)
                try:
                    user_input = input("Введите номер пункта: ")
                    option = int(user_input)
                    if option < 1 or option > len(currentMenuEntries):
                        raise ValueError
                except ValueError:
                    print(user_input, " - некорректный номер пункта.") # type: ignore
                    continue
                currentMenuEntries[option - 1].on_selected(self)
                break

    def message(self: Self, message: str):
        print(message)

    def input[T](self: Self, prompt: str, convert: Callable[[str], T], validate: Callable[[T], bool], errorMessage: str) -> T | None:
        while True:
            try:
                user_input = input(prompt)
                result : T = convert(user_input)
                if not validate(result):
                    raise ValueError
                return result
            except ValueError:
                print(errorMessage)
            except KeyboardInterrupt:
                return None