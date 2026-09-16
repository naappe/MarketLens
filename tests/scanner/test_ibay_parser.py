from scanner.ibay_v4 import listing_id, price_from_text, extract_page_html


def test_listing_id_matches_legacy_ibay_urls():
    assert listing_id("https://ibay.com.mv/iphone-15-pro-o12345.html") == "12345"
    assert listing_id("https://ibay.com.mv/not-a-listing.html") is None


def test_price_parser_matches_legacy_formats():
    assert price_from_text("MVR 12,500") == 12500.0
    assert price_from_text("RF. 999.50") == 999.50
    assert price_from_text("No price") is None


def test_extract_page_keeps_longest_title_and_wanted_intent():
    html = '''
    <html><body>
      <div>MVR 1,500 <a href="/phone-o42.html">Phone</a></div>
      <div>MVR 1,500 <a href="/phone-o42.html">Apple Phone 128GB</a></div>
    </body></html>
    '''
    items = extract_page_html(html, "https://ibay.com.mv/wanted-b1.html", "wanted")
    assert len(items) == 1
    assert items[0]["listing_id"] == "42"
    assert items[0]["title"] == "Apple Phone 128GB"
    assert items[0]["url"] == "https://ibay.com.mv/phone-o42.html"
    assert items[0]["type"] == "wanted"
    assert items[0]["price"] == 1500.0


def test_extract_page_keeps_listing_summary_context_for_job_analysis():
    html = '''
    <html><body>
      <div>We are hiring a cashier. WhatsApp 7844422. <a href="/cashier-o99.html">Cashier</a></div>
    </body></html>
    '''
    items = extract_page_html(html, "https://ibay.com.mv/jobs-b55_0.html", "category")
    assert "We are hiring a cashier" in items[0]["summary"]
    assert "7844422" in items[0]["summary"]
