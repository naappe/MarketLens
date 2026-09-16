import unittest

class V431ClassificationRegression(unittest.TestCase):

    def test_vehicle_source_beats_incidental_baby_word(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify("Baby blue Toyota Aqua", "Vehicles > Cars", "sale")[:2],
            ("Vehicles", "Cars")
        )

    def test_stroller_source_is_baby_gear(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify(
                "GYMAX Baby Foldable Stroller, Adjustable Backrest Pushchair with Safety Belt",
                "Strollers & Walkers", "sale"
            )[:2],
            ("Baby & Kids", "Baby Gear")
        )

    def test_nursery_decor_is_baby_nursery(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify("Baby Bed Bell Set", "Nursery Decor", "sale")[:2],
            ("Baby & Kids", "Nursery")
        )

    def test_baby_cot_overrides_generic_furniture_source(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify(
                "IKEA SNIGLAR Baby Cot + Mattress Used, Good Condition",
                "Furniture & Bedding", "sale"
            )[:2],
            ("Baby & Kids", "Nursery")
        )

    def test_baby_mattress_overrides_generic_furniture_source(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify("Very new Soft Baby mattress", "Furniture & Bedding", "sale")[:2],
            ("Baby & Kids", "Nursery")
        )

    def test_playpen_overrides_generic_furniture_source(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify("Foldable KIDS Playpen, Baby Play pen", "Furniture & Bedding", "sale")[:2],
            ("Baby & Kids", "Baby Gear")
        )

    def test_portable_ac_stays_home_appliance(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify("portable AC 12000btu", "Furniture & Bedding", "sale")[:2],
            ("Home & Living", "Appliances")
        )

    def test_iphone_is_electronics_phone_without_source(self):
        from scanner.classifier_v431 import classify
        self.assertEqual(
            classify("Apple iPhone 15 Pro Max 256GB", "", "sale")[:2],
            ("Electronics", "Phones")
        )

    def test_wanted_remains_intent_not_category(self):
        from scanner.classifier_v431 import classify
        cat, sub, intent, _, _ = classify("Wanted iPhone 15 Pro", "Mobile Phones", "wanted")
        self.assertEqual(cat, "Electronics")
        self.assertEqual(sub, "Phones")
        self.assertEqual(intent, "Wanted")

if __name__ == "__main__":
    unittest.main()