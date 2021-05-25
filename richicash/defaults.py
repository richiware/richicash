# Copyright 2021 Ricardo González
# Licensed under the Apache License, Version 2.0

from pathlib import Path
import yaml

class Defaults:
    transactional_accounts = ""
    cards = ""

    def __init__(self):
        defaults_path = Path.home() / '.config/richicash/defaults.yaml'
        if not defaults_path.is_file():
            return

        defaults_content = defaults_path.read_text()
        yaml_content = yaml.safe_load(defaults_content)
        if 'transactional-accounts' in yaml_content:
            self.transactional_accounts = yaml_content['transactional-accounts']
        if 'cards' in yaml_content:
            self.cards = yaml_content['cards']
