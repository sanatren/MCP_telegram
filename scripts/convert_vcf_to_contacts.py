#!/usr/bin/env python3
"""
Convert VCF contacts file to contacts.json
Extracts name and phone number from VCF format
"""

import re
import json
import os


def parse_vcf_to_json(vcf_path, output_json_path):
    """Parse VCF file and create contacts.json"""

    contacts = {}

    with open(vcf_path, 'r', encoding='utf-8', errors='ignore') as f:
        current_name = None
        current_phone = None

        for line in f:
            line = line.strip()

            # Extract full name
            if line.startswith('FN:'):
                current_name = line.replace('FN:', '').strip()

            # Extract phone number
            elif line.startswith('TEL'):
                # Extract number after colon
                phone_match = re.search(r':(.+)$', line)
                if phone_match:
                    current_phone = phone_match.group(1).strip()

                    # Clean phone number: remove spaces, dashes, etc.
                    current_phone = re.sub(r'[\s\-\(\)]', '', current_phone)

                    # Add +91 if it's 10 digits (Indian number without country code)
                    if current_phone and len(current_phone) == 10 and current_phone.isdigit():
                        current_phone = '+91' + current_phone
                    elif current_phone and not current_phone.startswith('+'):
                        # Try adding +91 for numbers without country code
                        if len(current_phone) >= 10:
                            current_phone = '+91' + current_phone[-10:]

            # End of card - save contact
            elif line == 'END:VCARD' and current_name and current_phone:
                # Create a clean key from name (lowercase, remove special chars)
                key = re.sub(r'[^a-z0-9\s]', '', current_name.lower())
                key = re.sub(r'\s+', '_', key).strip('_')

                # Skip if key is empty
                if key:
                    # If duplicate key, add number suffix
                    original_key = key
                    counter = 2
                    while key in contacts:
                        key = f"{original_key}_{counter}"
                        counter += 1

                    contacts[key] = current_phone

                # Reset for next contact
                current_name = None
                current_phone = None

    # Save to JSON
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)

    print(f"✅ Converted {len(contacts)} contacts to {output_json_path}")
    print(f"\nSample contacts:")
    for i, (name, phone) in enumerate(list(contacts.items())[:10]):
        print(f"  {name}: {phone}")

    return contacts


if __name__ == "__main__":
    vcf_path = os.path.join(os.path.dirname(__file__), '..', 'Contacts.vcf')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'contacts.json')

    parse_vcf_to_json(vcf_path, output_path)
