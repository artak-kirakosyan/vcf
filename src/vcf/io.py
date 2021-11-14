from typing import List

from vcf.utils.models import VCFContact


def parse_vcf_file(file_path) -> List[VCFContact]:
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
        file_name: str,
        version: float = 3.0,
        include_unprocessed_values: bool = False,
):
    vcf_content = ""
    for contact in contacts:
        try:
            vcf_content += contact.to_vcf(
                version=version,
                include_other_info=include_unprocessed_values
            )
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
