from scanner.cloud_store import tracked_changes


def test_missing_new_price_preserves_existing_price_and_is_not_a_price_change():
    old = {"title":"Phone","price_mvr":1200,"category_id":"a","status":"active","url":"u","listing_type":"for_sale","subcategory":"Phones","classification_confidence":88,"classification_reason":"strong title","source_category":"Mobile Phones","market_intent":"For Sale"}
    new = dict(old)
    new["price_mvr"] = None
    changed, merged = tracked_changes(old, new)
    assert merged["price_mvr"] == 1200
    assert "price_mvr" not in changed


def test_category_or_price_change_is_tracked():
    old = {"title":"Phone","price_mvr":1200,"category_id":"a","status":"active","url":"u","listing_type":"for_sale","subcategory":"Phones","classification_confidence":88,"classification_reason":"strong title","source_category":"Mobile Phones","market_intent":"For Sale"}
    new = dict(old, price_mvr=1300, category_id="b")
    changed, _ = tracked_changes(old, new)
    assert set(changed) >= {"price_mvr", "category_id"}


def test_job_direction_change_is_tracked():
    old = {"title":"Cashier","price_mvr":None,"category_id":"a","status":"active","url":"u","listing_type":"for_sale","subcategory":"Jobs","classification_confidence":88,"classification_reason":"source","source_category":"Jobs","market_intent":"For Sale","job_direction":"Other","job_role":"cashier","job_salary_min_mvr":None,"job_salary_max_mvr":None,"public_phone":None,"public_email":None}
    new = dict(old, job_direction="Hiring")
    changed, _ = tracked_changes(old, new)
    assert "job_direction" in changed
