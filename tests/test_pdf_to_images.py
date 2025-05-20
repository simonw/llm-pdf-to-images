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


def test_large_pdf_to_images_50():
    path = os.path.join(os.path.dirname(__file__), "hundred-pages.pdf")
    attachments = pdf_to_images_loader(path + "?image_count_constraint=50")
    assert isinstance(attachments, list)
    assert len(attachments) == 50
    assert all(isinstance(attachment, llm.Attachment) for attachment in attachments)
    assert attachments[0].path.endswith("page_001.jpg")
    # The 2nd image should have page 3, as the first image covers pages 1-2
    assert attachments[1].path.endswith("page_003.jpg")
    # Now delete them
    out_dir = os.path.dirname(attachments[0].path)
    shutil.rmtree(out_dir)


def test_large_pdf_to_images_40():
    path = os.path.join(os.path.dirname(__file__), "hundred-pages.pdf")
    attachments = pdf_to_images_loader(path + "?image_count_constraint=40")
    assert isinstance(attachments, list)
    assert len(attachments) == 34
    assert all(isinstance(attachment, llm.Attachment) for attachment in attachments)
    assert attachments[0].path.endswith("page_001.jpg")
    # The 2nd image should have page 4, as the first image covers pages 1-3
    assert attachments[1].path.endswith("page_004.jpg")
    # Now delete them
    out_dir = os.path.dirname(attachments[0].path)
    shutil.rmtree(out_dir)
