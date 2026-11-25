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
        """
        Повертає список контактів, яких потрібно привітати
        протягом наступних 7 днів (включно з сьогоднішнім).
        Якщо день народження припадає на вихідні,
        привітання переноситься на понеділок.
        """
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
    """
    Завантажує адресну книгу з файлу.

    Якщо файл ще не існує,