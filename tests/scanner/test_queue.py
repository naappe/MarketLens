from scanner.cloud_store import sort_sections


def test_unscanned_sections_rotate_before_old_scanned_sections():
    sections = [
        {"id":"3","name":"C","priority":100,"last_scan_at":"2026-09-16T01:00:00+00:00"},
        {"id":"2","name":"B","priority":100,"last_scan_at":None},
        {"id":"1","name":"Wanted","priority":10,"last_scan_at":None},
        {"id":"4","name":"D","priority":100,"last_scan_at":"2026-09-15T01:00:00+00:00"},
    ]
    assert [x["id"] for x in sort_sections(sections)] == ["1", "2", "4", "3"]
