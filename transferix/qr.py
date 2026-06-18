from os import environ

try:
    import qrcode
    from qrcode.image.svg import SvgPathImage

    enable_qrcode = bool(environ.get('TRANSFERIX_ENABLE_QR'))
except ImportError:
    enable_qrcode = False


def qrcode_html(text: str) -> str:
    if not enable_qrcode:
        return ''
    qr = qrcode.QRCode(image_factory=SvgPathImage, box_size=15, border=4)
    qr.add_data(text)
    return qr.make_image(fill_color="black", back_color="white").to_string().decode()
