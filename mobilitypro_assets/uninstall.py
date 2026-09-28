from mobilitypro_assets.install import REFERENCE_TYPE, get_reference_type_options, set_reference_type_options

def before_uninstall():
    reset_journal_entry_account_reference_type_field()

def reset_journal_entry_account_reference_type_field():
    options = get_reference_type_options()
    if REFERENCE_TYPE not in options:
        return
    set_reference_type_options([option for option in options if option != REFERENCE_TYPE])
