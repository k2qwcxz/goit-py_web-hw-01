import pickle
from collections import UserDict
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod

WEEKDAYS_UA = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця", 'Субота', 'Неділя']


class View(ABC):
    
    @abstractmethod
    def show(self, text: str):
        pass
    
    @abstractmethod
    def error(self, text: str):
        pass
    
    @abstractmethod
    def input_command(self) -> str:
        pass

class EmojiView(View):
    
    def show(self, text: str):
        print(f"✅ {text}")
    
    def error(self, text: str):
        print(f"❌ {text}")
    
    def input_command(self) -> str:
        return input("➤ ")


class SimpleView(View):
    
    def show(self, text: str):
        print(f"[OK] {text}")
    
    def error(self, text: str):
        print(f"[ERROR] {text}")
    
    def input_command(self) -> str:
        return input(">> ")


class MinimalView(View):
    
    def show(self, text: str):
        print(text)
    
    def error(self, text: str):
        print(f"Error: {text}")
    
    def input_command(self) -> str:
        return input("> ")


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name cannot be empty")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not (isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be exactly 10 digits")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Birthday must be a string in format DD.MM.YYYY")
        val = value.strip()
        try:
            datetime.strptime(val, "%d.%m.%Y") 
        except ValueError:
            raise ValueError("Birthday must be in format DD.MM.YYYY")
        super().__init__(val)

    def __str__(self):
        return self.value


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number: str):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def find_phone(self, phone_number: str):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def edit_phone(self, old_number: str, new_number: str):
        phone = self.find_phone(old_number)
        if phone:
            Phone(new_number)
            phone.value = new_number
            return True
        raise ValueError("Old phone number not found")

    def add_birthday(self, birthday_str: str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones = ", ".join([p.value for p in self.phones]) if self.phones else "—"
        bd = self.birthday.__str__() if self.birthday else "—"
        return f"{self.name.value}: {phones} | Birthday: {bd}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def add_contact(self, name: str, phone: str):
        if name in self.data:
            rec = self.data[name]
            rec.add_phone(phone)
        else:
            rec = Record(name)
            rec.add_phone(phone)
            self.add_record(rec)

    def change_contact(self, name: str, old_phone: str, new_phone: str):
        if name not in self.data:
            raise KeyError("Contact not found.")
        rec = self.data[name]
        old = rec.find_phone(old_phone)
        if not old:
            raise ValueError("Old phone number not found for this contact.")
        Phone(new_phone)
        old.value = new_phone
        return True

    def get_phone(self, name: str) -> str:
        if name not in self.data:
            raise KeyError("Contact not found.")
        rec = self.data[name]
        if not rec.phones:
            return "No phones set for this contact."
        return ", ".join([p.value for p in rec.phones])

    def add_birthday(self, name: str, bday_str: str):
        if name not in self.data:
            raise KeyError("Contact not found.")
        self.data[name].add_birthday(bday_str)

    def get_birthday(self, name: str):
        if name not in self.data:
            raise KeyError("Contact not found.")
        b = self.data[name].birthday
        if not b:
            raise ValueError("Birthday not set for this contact.")
        return b.value 

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        return "\n".join([str(rec) for rec in self.data.values()])


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()
    except Exception:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as ve:
            return str(ve)
        except IndexError:
            return "Missing arguments."
        except Exception as e:
            return str(e)
    return inner


def parse_input(user_input):
    if not user_input.strip():
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args


@input_error
def add_contact_cmd(args, book: AddressBook):
    if len(args) != 2:
        return "Use: add [name] [phone]"
    name, phone = args
    book.add_contact(name, phone)
    return "Contact added."


@input_error
def change_contact_cmd(args, book: AddressBook):
    if len(args) != 3:
        return "Use: change [name] [old_phone] [new_phone]"
    name, old_phone, new_phone = args
    book.change_contact(name, old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone_cmd(args, book: AddressBook):
    if len(args) != 1:
        return "Use: phone [name]"
    name = args[0]
    return book.get_phone(name)


@input_error
def add_birthday_cmd(args, book: AddressBook):
    if len(args) != 2:
        return "Use: add-birthday [name] [DD.MM.YYYY]"
    name, bstr = args
    try:
        datetime.strptime(bstr, "%d.%m.%Y")
    except ValueError:
        raise ValueError("Birthday must be DD.MM.YYYY")
    book.add_birthday(name, bstr)
    return "Birthday added."


@input_error
def show_birthday_cmd(args, book: AddressBook):
    if len(args) != 1:
        return "Use: show-birthday [name]"
    name = args[0]
    return book.get_birthday(name)


def main():
    book = load_data()
    view = SimpleView()    
    
    print("Welcome to Contact Bot!")
    print("Commands: add, change, phone, all, add-birthday, show-birthday, close")

    try:
        while True:
            user_input = view.input_command()
            command, args = parse_input(user_input)

            if command == "":
                view.error("Please enter a command.")
                continue

            if command in ["close", "exit", "good"]:
                view.show("Good bye!")
                break
            elif command == "hello":
                view.show("How can I help you?")
            elif command == "add":
                result = add_contact_cmd(args, book)
                if "Use:" in result or len(result) > 50:
                    view.error(result)
                else:
                    view.show(result)
            elif command == "change":
                result = change_contact_cmd(args, book)
                if "Use:" in result:
                    view.error(result)
                else:
                    view.show(result)
            elif command == "phone":
                result = show_phone_cmd(args, book)
                view.show(f"Phone: {result}")
            elif command == "all":
                view.show(str(book))
            elif command == "add-birthday":
                result = add_birthday_cmd(args, book)
                if "Use:" in result:
                    view.error(result)
                else:
                    view.show(result)
            elif command == "show-birthday":
                result = show_birthday_cmd(args, book)
                view.show(f"Birthday: {result}")
            else:
                view.error("Unknown command.")
    finally:
        save_data(book)


if __name__ == "__main__":
    main()