import os
import tempfile
import io
from PIL import Image
import fitz
from urllib.parse import urlparse, parse_qs
import llm


@llm.hookimpl
def register_fragment_loaders(register):
    """
    Register the "pdf-to-images" fragment loader.
    Usage: pdf-to-images:/path/to/file.pdf?dpi=300&format=jpg&quality=80&image_count_constraint=50
    """
    register("pdf-to-images", pdf_to_images_loader)


def pdf_to_images_loader(argument: str):
    """
    Fragment loader "pdf-to-images:<path>?dpi=N&format=jpg|png&quality=Q&image_count_constraint=P"
      - dpi: render resolution (dots per inch), default 300
      - format: "jpg" (default) or "png"
      - quality: JPEG quality 1–100, default 30
      - image_count_constraint: Max number of images to create, concatenate pages where needed, default -1 (no concatenation)
    """
    parts = urlparse(argument)
    pdf_path = parts.path
    params = parse_qs(parts.query)

    # parse parameters
    dpi = int(params.get("dpi", ["300"])[0])
    img_format = params.get("format", ["jpg"])[0].lower()
    quality = int(params.get("quality", ["30"])[0])
    image_count_constraint = int(params.get("image_count_constraint", ["-1"])[0])

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

    num_pages = len(doc)

    if image_count_constraint > 0 and num_pages > image_count_constraint:
        # Round up to ensure we don't exceed the threshold
        compression_ratio = -(-num_pages // image_count_constraint)
    else:
        compression_ratio = 1

    # Create an in-memory list to hold images for possible stitching
    page_images = []

    # iterate over pages
    for i in range(0, num_pages, compression_ratio):
        end_idx = min(i + compression_ratio, num_pages)

        # Process each page in the current group
        for j in range(i, end_idx):
            page = doc[j]
            # Use get_pixmap with correct keyword arguments
            pix = page.get_pixmap(matrix=matrix, alpha=False)  # type: ignore

            if img_format == "jpg":
                # Save pixmap to temporary file with jpg_quality parameter
                image_bytes = pix.tobytes(output="jpeg", jpg_quality=quality)
                ext = "jpg"
            elif img_format == "png":
                image_bytes = pix.tobytes(output="png")
                ext = "png"
            else:
                raise ValueError(f"Unsupported image format: {img_format}")

            # Convert to PIL Image for potential stitching
            img = Image.open(io.BytesIO(image_bytes))
            page_images.append(img)

        # If we're compressing pages and have multiple images, stitch them
        if compression_ratio > 1 and len(page_images) > 1:
            # Stitch images vertically
            total_width = max(img.width for img in page_images)
            total_height = sum(img.height for img in page_images)

            stitched_img = Image.new("RGB", (total_width, total_height))

            y_offset = 0
            for img in page_images:
                stitched_img.paste(img, (0, y_offset))
                y_offset += img.height

            # Save the stitched image
            out_name = f"page_{i + 1:03d}.{ext}"
            out_path = os.path.join(out_dir, out_name)

            if img_format == "jpg":
                stitched_img.save(out_path, format="JPEG", quality=quality)
            else:
                stitched_img.save(out_path, format="PNG")
        else:
            # Just use the single image (no stitching needed)
            out_name = f"page_{i + 1:03d}.{ext}"
            out_path = os.path.join(out_dir, out_name)

            # Save the first image
            if page_images:
                if img_format == "jpg":
                    page_images[0].save(out_path, format="JPEG", quality=quality)
                else:
                    page_images[0].save(out_path, format="PNG")

        attachments.append(llm.Attachment(path=out_path))

        # Clear the images list for the next group
        page_images = []

    return attachments
