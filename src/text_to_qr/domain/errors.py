# TODO: RETURN ERROR MESSAGE WITH DTO
class QRCodeError(Exception):
    pass

class UnsupportedFormatError(QRCodeError):
    pass
