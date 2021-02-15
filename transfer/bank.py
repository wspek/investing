from transfer.institution import Institution


class BancoGalicia(Institution):
    def __init__(self):
        super(BancoGalicia, self).__init__("Banco Galicia")


class Rabobank(Institution):
    def __init__(self):
        super(Rabobank, self).__init__("Rabobank")
