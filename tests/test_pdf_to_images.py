import os
import shutil
import llm
from llm_pdf_to_images import pdf_to_images_loader


def test_pdf_to_images():
    path = os.path.join(os.path.dirname(__file__), "blank-pages.pdf")
    attachments = pdf_to_images_loader(path)
    assert isinstance(attachments, list)
    assert len(attachments) == 2
    assert all(isinstance(attachment, llm.Attachment) for attachment in attachments)
    assert attachments[0].path.endswith("page_001.jpg")
    assert attachments[1].path.endswith("page_002.jpg")
    # Now delete them
    out_dir = os.path.dirname(attachments[0].path)
    shutil.rmtree(out_dir)
