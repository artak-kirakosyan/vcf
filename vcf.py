import re
from typing import Set, List


class PhoneNumber:
    __types = set()
    __default_type = "CELL"
    __phone_line = "TEL;"
    __type_line = "TYPE="
    __phone_pattern = __phone_line + __type_line + r"(\w+):(.+)"
    __number_hash = 37
    __type_hash = 7

    def __init__(self, number: str, phone_type: str):
        self.number = number
        self.phone_type = phone_type

    def __repr__(self):
        rpr = "PhoneNumber(number=%s, phone_type=%s)" % (self.number, self.phone_type)
        return rpr

    def __str__(self):
        return f"{self.__phone_line}{self.__type_line}{self.phone_type}:{self.number}"

    def __eq__(self, other: "PhoneNumber"):
        if not isinstance(other, self.__class__):
            return False
        return self.number == other.number and self.phone_type == other.phone_type

    def __hash__(self):
        return hash(self.number) * self.__number_hash + hash(self.phone_type) * self.__type_hash

    @classmethod
    def from_vcf_line(cls, line: str, preserve_type: bool = False):
        match = re.match(cls.__phone_pattern, line)
        if match is None:
            raise ValueError("No line matched")
        groups = match.groups()
        try:
            phone_type = groups[0].upper()
            cls.__types.add(phone_type)
            phone_number = groups[1]
            phone_number = re.sub("[^+0-9]", "", phone_number)
        except IndexError:
            raise ValueError("Not enough info in the line") from None
        if not preserve_type:
            phone_type = cls.__default_type

        return cls(phone_type=phone_type, number=phone_number)


class VCFContact:
    __contact_begin = "BEGIN:VCARD"
    __contact_end = "END:VCARD"
    __vcf_version = "VERSION:"
    __category = "CATEGORIES:"
    __category_separator = ","
    __category_pattern = __category + r"(.+)"
    __full_name = "FN:"
    __name = "N:"
    __name_part_pattern = "(.*?)"
    __name_pattern_replacement = "%s;%s;%s;%s;%s"
    __name_pattern = __name + __name_pattern_replacement % (
        __name_part_pattern,
        __name_part_pattern,
        __name_part_pattern,
        __name_part_pattern,
        __name_part_pattern
    )
    __phone = "TEL;"

    def __init__(self):
        self.phones: Set[PhoneNumber] = set()
        self.other_info = set()
        self.categories = set()
        self.prefix = ""
        self.first_name = ""
        self.surname = ""
        self.middle_name = ""
        self.suffix = ""

    def __str__(self):
        return self.full_name + str(self.phones)

    @property
    def full_name_parts(self):
        return [
            self.prefix,
            self.first_name,
            self.middle_name,
            self.surname,
            self.suffix,
        ]

    @property
    def name_parts(self):
        return [
            self.surname,
            self.first_name,
            self.middle_name,
            self.prefix,
            self.suffix,
        ]

    @property
    def full_name(self):
        return " ".join([part for part in self.full_name_parts if part.strip() != ""])

    def get_full_name_line(self):
        return self.__full_name + self.full_name

    def get_name_line(self):
        return self.__name + self.__name_pattern_replacement % (*self.name_parts, )

    def add_line(self, line: str):
        if self.is_service_line(line):
            print("This is a service line, skipping")
            return
        if self.is_name_line(line):
            self.add_name(line)
            return
        if self.is_phone_line(line):
            self.add_phone(line)
            return
        if self.is_category_line(line):
            self.add_category(line)
            return
        if self.is_full_name_line(line):
            return

        self.other_info.add(line)

    def add_name(self, line: str):
        match = re.match(self.__name_pattern, line)
        if match is None:
            print("No name matched")
            return
        groups = match.groups()
        try:
            surname, first_name, middle_name, prefix, suffix = groups
        except ValueError:
            print("Invalid name line")
            return
        self.surname = surname
        self.first_name = first_name
        self.middle_name = middle_name
        self.prefix = prefix
        self.suffix = suffix

    def add_category(self, line: str):
        match = re.match(self.__category_pattern, line)
        if match is None:
            print("No category matched.")
            return
        groups = match.groups()
        try:
            categories = groups[0]
        except IndexError:
            print("No category matched.")
            return
        categories = categories.split(self.__category_separator)
        self.categories.update(categories)

    def add_phone(self, line: str):
        try:
            phone = PhoneNumber.from_vcf_line(line)
        except ValueError:
            print("Failed to create phone number")
            return
        else:
            self.phones.add(phone)

    def get_version(self, version: float = 3.0):
        version = self.__vcf_version + "%.1f" % version
        return version

    def get_sorted_phones(self):
        return sorted([str(phone) for phone in self.phones])

    def get_categories(self):
        if self.categories:
            return self.__category + self.__category_separator.join(self.categories)
        else:
            return None

    def is_empty(self):
        return len(self.phones) == 0

    def _to_vcf(self, version: float = 3.0, include_other_info: bool = False):
        vcf = [
            self.__contact_begin,
            self.get_version(version=version),
            self.get_full_name_line(),
            self.get_name_line(),
        ]
        categories = self.get_categories()
        if categories:
            vcf.append(categories)

        vcf.extend(self.get_sorted_phones())
        if include_other_info:
            vcf.extend(self.other_info)
        vcf.extend([self.__contact_end, "", ""])

        return "\n".join(vcf)

    def to_vcf(self, *args, **kwargs):
        if self.is_empty():
            raise ValueError("Empty contact")

        return self._to_vcf(*args, **kwargs)

    @classmethod
    def is_end_of_contact(cls, line: str):
        return line == cls.__contact_end

    @classmethod
    def is_start_of_contact(cls, line: str):
        return line == cls.__contact_begin

    @classmethod
    def is_version_line(cls, line: str):
        return line.startswith(cls.__vcf_version)

    @classmethod
    def is_service_line(cls, line: str):
        is_start = cls.is_start_of_contact(line)
        is_end = cls.is_end_of_contact(line)
        is_version = cls.is_version_line(line)
        return is_start or is_end or is_version

    @classmethod
    def is_phone_line(cls, line: str):
        return line.startswith(cls.__phone)

    @classmethod
    def is_category_line(cls, line: str):
        return line.startswith(cls.__category)

    @classmethod
    def is_name_line(cls, line: str):
        return line.startswith(cls.__name)

    @classmethod
    def is_full_name_line(cls, line: str):
        return line.startswith(cls.__full_name)


def parse_vcf_file(file_path='removed_duplicates.vcf') -> List[VCFContact]:
    with open(file_path) as f:
        content = f.read()
        vcf_lines = content.split("\n")

    parsed_contracts = []
    current_contact = []
    for line in vcf_lines:
        if VCFContact.is_end_of_contact(line):
            parsed_contracts.append(current_contact)
            current_contact = []
            continue
        if VCFContact.is_service_line(line):
            continue
        current_contact.append(line)

    vcf_contacts = []
    for contact_lines in parsed_contracts:
        contact = VCFContact()
        vcf_contacts.append(contact)
        for line in contact_lines:
            contact.add_line(line)

    return vcf_contacts


def write_contacts_to_vcf_file(
        contacts: List[VCFContact],
        file_name="cleaned.vcf",
        version: float = 3.0,
        include_unprocessed_values: bool = False,
):
    vcf_content = ""
    for contact in contacts:
        try:
            vcf_content += contact.to_vcf(version=version, include_other_info=include_unprocessed_values)
        except ValueError:
            print("Empty contact: %s" % contact)
    with open(file_name, "w") as f:
        f.write(vcf_content)


def clean_vcf(file_path: str):
    contacts = parse_vcf_file(file_path=file_path)
    write_contacts_to_vcf_file(
        contacts=contacts,
        file_name=file_path,
        version=3.0,
        include_unprocessed_values=False,
    )
