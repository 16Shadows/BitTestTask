def converter_string(x : str) -> str:
    '''Функция-конвертер для input_validated, убирающая whitespace-символы из начала и конца строки'''
    return x.strip()

def converter_int(x: str) -> int:
    '''Функция-конвертер для input_validated, парсящая строку как целое число'''
    return int(x)

def validator_string_not_empty(x : str) -> bool:
    '''Функция-валидатор для input_validated, проверяющая, не пустая ли строка'''
    return len(x) > 0

def validator_always(_ : object) -> bool:
    '''Функция-валидатор для input_validate, принимающая любое значение как валидное'''
    return True

def validator_int_range(value: int, min: int | None = None, max: int | None = None) -> bool:
    '''Функция-валидатор для input_validate, проверяющая, находится ли число в диапазоне (включительно)
    
    Аргументы:
    value : int - значение для проверки
    min : int | None - нижняя граница. Если None, то нижней границы нет.
    max : int | None - верхняя граница. Если None, то верхней границы нет.
    '''
    return (min is None or min <= value) and (max is None or value <= max)