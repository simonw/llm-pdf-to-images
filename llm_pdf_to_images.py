import os
import tempfile
import fitz
from urllib.parse import urlparse, parse_qs
import llm


@llm.hookimpl
def register_fragment_loaders(register):
    """
    Register the "pdf-to-images" fragment loader.
    Usage: pdf-to-images:/path/to/file.pdf?dpi=300&format=jpg&quality=80&pages=1,3-5
    """
    register("pdf-to-images", pdf_to_images_loader)


def parse_pages(pages_str):
    pages = set()
    for part in pages_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return pages


def pdf_to_images_loader(argument: str):
    """
    Fragment loader "pdf-to-images:<path>?dpi=N&format=jpg|png&quality=Q&pages=P"
      - dpi: render resolution (dots per inch), default 300
      - format: "jpg" (default) or "png"
      - quality: JPEG quality 1–100, default 30
      - pages: specific pages or page ranges, e.g., "1,3-5"
    """
    parts = urlparse(argument)
    pdf_path = parts.path
    params = parse_qs(parts.query)

    # parse parameters
    dpi = int(params.get("dpi", ["300"])[0])
    img_format = params.get("format", ["jpg"])[0].lower()
    quality = int(params.get("quality", ["30"])[0])
    pages = parse_pages(params.get("pages", [""])[0]) if "pages" in params else None

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
        if pages and page_number not in pages:
            continue

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
