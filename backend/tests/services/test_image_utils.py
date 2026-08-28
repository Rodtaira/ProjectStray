import io

from PIL import Image

from app.services.image_utils import process_photo


def _make_jpeg_with_gps_exif() -> bytes:
    """Monta uma imagem JPEG mínima com metadado EXIF de GPS embutido —
    é esse dado que precisa sumir depois do processamento."""
    image = Image.new("RGB", (10, 10), color="red")

    exif = image.getexif()
    gps_ifd = {
        1: "N",  # GPSLatitudeRef
        2: (15.0, 46.0, 48.0),  # GPSLatitude (graus, minutos, segundos)
        3: "W",  # GPSLongitudeRef
        4: (47.0, 55.0, 48.0),  # GPSLongitude
    }
    exif[34853] = gps_ifd  # tag do GPSInfo

    output = io.BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


class TestProcessPhoto:
    def test_returns_a_valid_jpeg(self):
        original = _make_jpeg_with_gps_exif()

        processed = process_photo(original)

        result = Image.open(io.BytesIO(processed))
        assert result.format == "JPEG"

    def test_strips_gps_exif_data(self):
        original = _make_jpeg_with_gps_exif()

        processed = process_photo(original)

        result = Image.open(io.BytesIO(processed))
        assert result.getexif().get(34853) is None

    def test_strips_all_exif_data(self):
        original = _make_jpeg_with_gps_exif()

        processed = process_photo(original)

        result = Image.open(io.BytesIO(processed))
        assert len(result.getexif()) == 0

    def test_preserves_image_dimensions(self):
        image = Image.new("RGB", (40, 20), color="blue")
        output = io.BytesIO()
        image.save(output, format="PNG")

        processed = process_photo(output.getvalue())

        result = Image.open(io.BytesIO(processed))
        assert result.size == (40, 20)

    def test_converts_png_to_jpeg(self):
        image = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))
        output = io.BytesIO()
        image.save(output, format="PNG")

        processed = process_photo(output.getvalue())

        result = Image.open(io.BytesIO(processed))
        assert result.format == "JPEG"