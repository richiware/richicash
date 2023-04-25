from pathlib import Path
import re
import yaml

from .defaults import Defaults

class TransactionalAccounts:
    transactional_accounts = dict()
    cards = dict()

    def __init__(
            self,
            defaults: Defaults):
        """
        Parse the yaml file containing the relations between account movements
        and the related name of transactional accounts.
        """
        file_path = Path(defaults.transactional_accounts)
        if file_path.is_file():
            file_content = file_path.read_text()
            self.transactional_accounts = yaml.safe_load(file_content)

        file_path = Path(defaults.cards)
        if file_path.is_file():
            file_content = file_path.read_text()
            self.cards = yaml.safe_load(file_content)


    def deduce(
            self,
            descr: str,
            ref: str):
        """ Return the name of the transactional account for a description."""
        account_name = "Descuadre-EUR"

        if descr == 'REINT.CAJERO' or descr == 'CAJERO SERVIRED':
            try:
                account_name = self.cards[ref]["extract_money_to"]
            except Exception:
                pass

            if "Descuadre-EUR" == account_name and "********" in ref:
                try:
                    match = [value for key, value
                             in self.cards.items()
                             if key[:4] == ref[:4] and key[-4] == ref[-4]]
                    account_name = match[0]["extract_money_to"]
                except Exception:
                    print("Error getting card info for " + ref)
        else:
            try:
                account_name = self.transactional_accounts[descr]
            except Exception:
                pass

            if "Descuadre-EUR" == account_name:
                try:
                    match = [value for key, value
                             in self.transactional_accounts.items()
                             if key in descr]
                    account_name = match[0]
                except Exception:
                    pass

        return account_name


    def get_card_account(
            self,
            ref: str):
        """ Return the account for a specific card. """
        return self.cards[ref]["account"]
