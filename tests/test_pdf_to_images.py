import os
import shutil
import subprocess
import sys
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


def test_llm_version_does_not_emit_fitz_deprecation():
    result = subprocess.run(
        [sys.executable, "-m", "llm", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.startswith("python -m llm, version ")
    assert result.stderr == ""
