import os
import tempfile
import fitz
from urllib.parse import urlparse, parse_qs
import llm


@llm.hookimpl
def register_fragment_loaders(register):
    """
    Register the "pdf-to-images" fragment loader.
    Usage: pdf-to-images:/path/to/file.pdf?dpi=300&format=jpg&quality=80
    """
    register("pdf-to-images", pdf_to_images_loader)


def pdf_to_images_loader(argument: str):
    """
    Fragment loader "pdf-to-images:<path>?dpi=N&format=jpg|png&quality=Q"
      - dpi: render resolution (dots per inch), default 300
      - format: "jpg" (default) or "png"
      - quality: JPEG quality 1–100, default 30
    """
    parts = urlparse(argument)
    pdf_path = parts.path
    params = parse_qs(parts.query)

    # parse parameters
    dpi = int(params.get("dpi", ["300"])[0])
    img_format = params.get("format", ["jpg"])[0].lower()
    quality = int(params.get("quality", ["30"])[0])

    if not os.path.exists(pdf_path):
        raise ValueError(f"PDF file not found: {pdf_path}")

    # open PDF
    doc = fitz.open(pdf_path)

    # compute scale matrix
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)

    # prepare output directory
    out_dir = tempfile.mkdtemp(prefix="llm_pdf_to_images_")

    attachments = []
    for page_number, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix)

        if img_format in ("jpg", "jpeg"):
            image_bytes = pix.tobytes(output="jpg", jpg_quality=quality)
            ext = "jpg"
        elif img_format == "png":
            image_bytes = pix.tobytes(output="png")
            ext = "png"
        else:
            raise ValueError(f"Unsupported image format: {img_format}")

        out_name = f"page_{page_number:03d}.{ext}"
        out_path = os.path.join(out_dir, out_name)
        with open(out_path, "wb") as img_file:
            img_file.write(image_bytes)

        attachments.append(llm.Attachment(path=out_path))

    return attachments
