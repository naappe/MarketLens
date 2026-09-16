from scanner.classifier_v431 import classify


def test_stroller_source_is_baby_gear():
    assert classify("New stroller seat belt", "Strollers & Walkers", "sale")[:2] == ("Baby & Kids", "Baby Gear")


def test_nursery_decor_is_baby_nursery():
    assert classify("Baby Bed Bell Set", "Nursery Decor", "sale")[:2] == ("Baby & Kids", "Nursery")


def test_baby_cot_overrides_generic_furniture_source():
    assert classify("IKEA SNIGLAR Baby Cot + Mattress Used, Good Condition", "Furniture & Bedding", "sale")[:2] == ("Baby & Kids", "Nursery")


def test_portable_ac_stays_home_appliance():
    assert classify("portable AC 12000btu", "Furniture & Bedding", "sale")[:2] == ("Home & Living", "Appliances")


def test_iphone_is_electronics_phone_without_source():
    assert classify("Apple iPhone 15 Pro Max 256GB", "", "sale")[:2] == ("Electronics", "Phones")


def test_wanted_remains_intent_not_category():
    cat, sub, intent, _, _ = classify("Wanted iPhone 15 Pro", "Mobile Phones", "wanted")
    assert (cat, sub, intent) == ("Electronics", "Phones", "Wanted")
