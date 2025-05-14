def get_pip_info(pair):
    """Returns (pip_multiplier, pip_value_per_standard_lot)"""
    pair = pair.upper()

    # Special cases
    if pair.startswith("XAU") or pair.startswith("GOLD"):
        return 1, 10  # Gold: 1 pip = 1.00; $10 per pip
    if pair.startswith("XAG"):  # Silver
        return 1, 50
    if pair.endswith("JPY"):
        return 100, 9.5  # Most JPY pairs: 1 pip = 0.01; $9.5 per pip
    else:
        return 10000, 10  # Standard pairs like EURUSD
