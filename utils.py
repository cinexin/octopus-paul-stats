import unicodedata


def normalize(name):
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower().strip()
