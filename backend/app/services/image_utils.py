import io

from PIL import Image


def process_photo(image_bytes: bytes) -> bytes:
    """Remove todo metadado EXIF (inclusive geolocalização) e normaliza
    pra JPEG — nunca confiamos no metadado de um arquivo enviado pelo
    cliente. Reconstrói a imagem a partir dos pixels brutos em vez de só
    remover a tag EXIF, porque isso garante que nenhum metadado sobra
    escondido em outro lugar do arquivo.
    """
    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert("RGB")

    clean = Image.new("RGB", image.size)
    clean.putdata(list(image.getdata()))

    output = io.BytesIO()
    clean.save(output, format="JPEG", quality=85)
    return output.getvalue()