from scanner.link_search import canonical_url, extract_links, opportunity_score
from scanner.source_catalog import get_source


def test_canonical_url_removes_fragment():
    assert canonical_url("https://example.com/", "/jobs/1#top") == "https://example.com/jobs/1"


def test_opportunity_score_prioritizes_tenders_and_jobs():
    assert opportunity_score("Invitation to Tender", "/iulaan/123", ("tender",)) >= 40
    assert opportunity_score("Job Vacancy", "/jobs/99", ("job", "vacancy")) >= 40


def test_extract_links_filters_noise_and_external_urls():
    source = get_source("gazette")
    html = """
    <a href="/iulaan/123">Invitation to Bid - Supply of Equipment</a>
    <a href="/privacy">Privacy</a>
    <a href="https://example.com/tender">External Tender</a>
    """
    rows = extract_links(html, source)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://gazette.gov.mv/iulaan/123"
    assert rows[0]["score"] > 0
