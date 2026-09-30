import pymupdf


def read_pdf(file_path):
    """
    Read a PDF and return all extracted text.
    """

    document = pymupdf.open(file_path)

    text = ""

    for page in document:
        text += page.get_text() + "\n"

    document.close()

    return text