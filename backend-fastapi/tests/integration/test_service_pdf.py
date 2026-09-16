from scripts.preview_service_pdf import samples


def test_pdf_covers_unicode_links_lists_and_long_descriptions():
    generated = dict(samples())
    assert len(generated) == 4
    for pdf in generated.values():
        assert pdf.startswith(b'%PDF-')
        assert b'/FontFile2' in pdf  # Embedded Unicode-capable fonts.
    assert b'/URI' in generated['with-cover']
    assert generated['long'].count(b'/Type /Page\n') > 1
    assert b'/Subtype /Image' in generated['with-cover']
    assert b'/Subtype /Image' not in generated['without-cover']
