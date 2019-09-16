import base64
import io

import qrcode


def make_qr_code(text, encode_base64=True):
    """
    Convert the given text to a QR-code PNG image.
    If encode_base64==True, return base64-encoded image data (embed in `<img src>`);
    otherwise, return raw image file data as bytes (save to file).
    """
    qr = qrcode.QRCode(version=None)
    qr.add_data(text)
    qr.make(fit=True)  # is a Pillow Image
    image = qr.make_image(fill_color="black", back_color="white")
    f = io.BytesIO()
    image.save(f, format='PNG')
    f.seek(0)
    b = f.read()
    if encode_base64 is True:
        return base64.b64encode(b).decode('utf-8')
    else:
        return b
