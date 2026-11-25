import pickle
from collections import UserDict
from datetime import date, datetime, timedelta


# =========================
# Класи адресної книги
# =========================

class Field:
    """Базовий клас для полів запису."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Клас для зберігання імені контакту. Обов'язкове поле."""
    pass


class Phone(Field):
    """Клас для зберігання номера телефону. Номер має містити рівно 10 цифр."""

    def __init__(self, value):
        if not (len(value) == 10 and value.isdigit()):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """Клас для зберігання дня народження у форматі DD.MM.YYYY."""

    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(birthday)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    """Клас для зберігання інформації про контакт: ім'я, телефони, день народження."""

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        """Додає новий телефон до запису."""
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        """Видаляє телефон із запису."""
        phone_obj = self.find_phone(phone)
        if phone_obj is None:
            raise ValueError(f"Phone {phone} not found.")
        self.phones.remove(phone_obj)

    def edit_phone(self, old_phone, new_phone):
        """Замінює існуючий телефон на новий."""
        phone_obj = self.find_phone(old_phone)
        if phone_obj is None:
            raise ValueError(f"Phone {old_phone} not found.")
        new_phone_obj = Phone(new_phone)
        index = self.phones.index(phone_obj)
        self.phones[index] = new_phone_obj

    def find_phone(self, phone):
        """Шукає телефон у записі. Повертає об'єкт Phone або None."""
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj
        return None

    def add_birthday(self, birthday):
        """Додає (або замінює) день народження контакту."""
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones) or "no phones"
        text = f"Contact name: {self.name.value}, phones: {phones}"
        if self.birthday:
            text += f", birthday: {self.birthday}"
        return text


class AddressBook(UserDict):
    """Клас для зберігання та керування записами адресної книги."""

    DAYS_AHEAD = 7

    def add_record(self, record):
        """Додає запис до адресної книги."""
        self.data[record.name.value] = record

    def find(self, name):
        """Шукає запис за ім'ям. Повертає Record або None."""
        return self.data.get(name)

    def delete(self, name):
        """Видаляє запис за ім'ям, якщо він існує."""
        self.data.pop(name, None)

    @staticmethod
    def _birthday_in_year(birthday, year):
        """Повертає дату дня народження у вказаному році (29.02 -> 01.03)."""
        try:
            return birthday.replace(year=year)
        except ValueError:
            return date(year, 3, 1)

    def get_upcoming_birthdays(self):
        """Повертає контакти для привітання на 7 днів уперед (вихідні -> понеділок)."""
        today = date.today()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value
            birthday_this_year = self._birthday_in_year(birthday, today.year)
            if birthday_this_year < today:
                birthday_this_year = self._birthday_in_year(birthday, today.year + 1)

            days_until = (birthday_this_year - today).days
            if 0 <= days_until < self.DAYS_AHEAD:
                congratulation_date = birthday_this_year
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                })

        return upcoming


# =========================
# Збереження та завантаження даних
# =========================

def save_data(book: AddressBook, filename: str = "addressbook.pkl") -> None:
    """Зберігає адресну книгу у файл за допомогою pickle."""
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename: str = "addressbook.pkl") -> AddressBook:
    """Завантажує адресну книгу з файлу. Якщо файлу немає — повертає нову порожню книгу."""
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()


# =========================
# Логіка бота
# =========================

def input_error(func):
    """Декоратор: перехоплює ValueError, KeyError, IndexError і повертає зрозуміле повідомлення."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return str(error)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command."

    return inner


def parse_input(user_input: str) -> tuple:
    """Розбирає введений рядок на команду (у нижньому регістрі) та аргументи."""
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook) -> str:
    """Додає новий контакт або новий телефон до існуючого контакту."""
    if len(args) < 2:
        raise ValueError("Give me name and phone please.")
    name, phone, *_ = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."

    record.add_phone(phone)
    return "Contact updated."


@input_error
def change_contact(args, book: AddressBook) -> str:
    """Змінює телефон контакту: change [ім'я] [старий] [новий]."""
    if len(args) < 3:
        raise ValueError("Give me name, old phone and new phone please.")
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook) -> str:
    """Показує телефони контакту."""
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if not record.phones:
        return "No phones for this contact."
    return "; ".join(p.value for p in record.phones)


def show_all(book: AddressBook) -> str:
    """Показує всі контакти з адресної книги."""
    if not book.data:
        return "No contacts saved."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook) -> str:
    """Додає день народження: add-birthday [ім'я] [DD.MM.YYYY]."""
    if len(args) < 2:
        raise ValueError("Give me name and birthday (DD.MM.YYYY) please.")
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook) -> str:
    """Показує день народження контакту."""
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if record.birthday is None:
        return "Birthday is not set for this contact."
    return str(record.birthday)


@input_error
def birthdays(args, book: AddressBook) -> str:
    """Показує, кого потрібно привітати протягом наступного тижня."""
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(
        f"{item['name']}: {item['congratulation_date']}" for item in upcoming
    )


def main() -> None:
    """Головний цикл бота: завантажує дані, приймає команди, зберігає дані при виході."""
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        if not user_input.strip():
            print("Invalid command.")
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()