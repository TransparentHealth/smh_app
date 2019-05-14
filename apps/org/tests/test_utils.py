from django.test import TestCase
from apps.org.utils import make_qr_code

fixtures = {
    'TEST_URL': 'http://sharemyhealthapp:8002/org/TestOrg/create-member/newmember-1/complete/NTA/56b-2936ae4d4ea599a9d3ac/',  # noqa
    'TEST_PNG_BASE64': 'iVBORw0KGgoAAAANSUhEUgAAAeoAAAHqAQAAAADjFjCXAAAEKUlEQVR4nO2dQY7jOAxFP8cCsrSBPkAdRb5BH6nQR5ob2EfJDaxlATb+LERLSmZWsRtdGX8uDAfWgxKAoER+WjHigM1/HaEB4cKFCxcuXLhw4efi5hZgNsAvIwCzYbM8ZExm+WJmZuN5swu/KB5JkguAuGwGJDN/sOwj5w8SQEeS5CN+cHbhF8WThy/+GgBEruCUAgB0NDMz8h7ACYCZhZNnF35t3D6zc3XEPGzGCZv5x48VNv7e2YVfAw9PnzkPfmeRWwDSDxqwGeOyBSKdOrvwa+M9ySnfrQBSyGutjf2anwLwDIPkevLswi+Jz2aWM9fP+402wu+AFIB4D7Ax3QhgyynsqbMLvxgOPlqOeuQKTuUuB7ee/7LprX+78D+FZ69DXJAT1Jw5ZCuLa1y6vP6SS0dO/eq1Fnmd8JfMg1ZPItI9zJ2wX8vFHTNbHiKvE/6qeQ4b72EF0oCcpc4fawDSjRbvJcvtPQYaAPCU2YVfEy+xrg1pvqVbfElFViSWrt3mKdYJf932xGBFdrOpd7+qrgegy4uwX3ZZTF4n/DXbVdVdX41LRy/QZf9rt3TucNrXCT9mdYUFSvoaF8CbAVjTjNZF5XXCj+I2pgBEflldSG1ER/6yAG9B6VcX/iO/VCUWfsByhkoAMKQBhn4LnEeA89B5vjp/EFmRjROAGhPf+7cL/1N4U69rCnSuUqxoLrVKl5NbrbDCj+H2eTcD0o2I9xsxD1Wl6PZsonfN32w4d3bhV8NbbaLEtb1K5ymFD8Eui6lyIvwYXmojXVMWzj1PsSy9vuC25TvlsMIPWLOvc+GBrA113sue3awUV6T+Cz9ku8qaDPS+YYDzzy0A/ZKfWVx+gPOwcJdgN+mwwo+YL6DLYwl42YObSxVr+7ZYlA4r/JDlWGdAt/ecIL88YZytjEohF+0sTlsg0nDS7MKviT8oYnW/9vC00WGfc423/u3CvwHOKd2I2QJsxN4ynG1PX23sv6zJNb7Plxf+tni/ojkAINeLdx3Wxn1UvftWX174++DtGhprB2fOMDo2L0/UwaqcCD+Go/Gw/+pqeux5cpV2kQ4r/JC5c9Vi8AKvDdfm9QlonkoRE35qrCs6bElkIx9bUNA1a628TvhrVisn/j5ObU/fG5/8fdia0gLa1wk/jhcJwkZsBmCzfNgEgN317jff9amrU/gxvOhgAKq0X9/4ry9PAHho7VSsE34Qj7sY6xEuBWD++DIb0eWi3cPmrhTtvsWXF/5u+HO9zo8z2WsoLAfrtN1Pi7IJ4WfiNla5K2/ubvSzirFZ3dfZ+DtmF34N/PmsTiAZvLUuDbD4N8DZOmL+2RHAFjgP0JuJwo9Yu5qWNvZyVlgeU895KnU9rbDCD9hzDltkMa/XoZx9svgQUl4n/JCZ/r1OuHDhwoULFy78f4H/A/VmHL7k5h5KAAAAAElFTkSuQmCC'  # noqa
}


class TestMakeQRCode(TestCase):
    def test_make_qr_code_defaults(self):
        """make_qr_code(url) with default parameters returns a base64-encoded PNG image string"""
        png_base64 = make_qr_code(fixtures['TEST_URL'])
        self.assertEqual(png_base64, fixtures['TEST_PNG_BASE64'])
