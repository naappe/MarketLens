from scanner.job_intelligence import classify_job_direction, extract_job_detail_html, job_match_score


def test_classifies_employer_listing_as_hiring():
    result = classify_job_direction(
        "Cashier (Maldivian)",
        "We are looking for a responsible cashier to join our team."
    )
    assert result == "Hiring"


def test_classifies_person_seeking_work_as_job_seeker():
    result = classify_job_direction(
        "JOB SEEKING CAFE / WAITRESS",
        "Reliable lady is currently looking for a job opportunity as waitress or cashier."
    )
    assert result == "Job Seeker"


def test_extracts_public_job_fields_from_detail_html():
    html = """
    <html><body>
      <h1>JOB VACANCY CASHIER</h1>
      <div>Location</div><div>Male City/Male</div>
      <div>Employer</div><div>Handuveli Private Limited</div>
      <div>Salary Range</div><div>Rf 5,001 to Rf 10,000</div>
      <div>Position Type</div><div>Full Time</div>
      <div class='description'>Interested candidates send CV to jobs@example.com or WhatsApp +960 9974859.</div>
    </body></html>
    """
    fields = extract_job_detail_html(html)
    assert fields["employer"] == "Handuveli Private Limited"
    assert fields["location"] == "Male City/Male"
    assert fields["position_type"] == "Full Time"
    assert fields["job_salary_min_mvr"] == 5001
    assert fields["job_salary_max_mvr"] == 10000
    assert fields["public_email"] == "jobs@example.com"
    assert fields["public_phone"] == "+9609974859"


def test_scores_cashier_hiring_against_cashier_job_seeker():
    hiring = {"title": "Female Cashier", "job_role": "cashier", "job_direction": "Hiring"}
    seeker = {"title": "Looking for cashier job", "job_role": "cashier", "job_direction": "Job Seeker"}
    assert job_match_score(hiring, seeker) >= 90


def test_does_not_match_two_hiring_listings():
    left = {"title": "Cashier", "job_role": "cashier", "job_direction": "Hiring"}
    right = {"title": "Need cashier", "job_role": "cashier", "job_direction": "Hiring"}
    assert job_match_score(left, right) == 0


def test_analyze_job_listing_returns_hiring_role_and_public_phone():
    from scanner.job_intelligence import analyze_job_listing
    fields = analyze_job_listing(
        "Cashier (Female / Maldivians)",
        "Need Cashiers. Message Viber / WhatsApp +9607844422 Salary Range Rf 5,001 to Rf 10,000",
    )
    assert fields["job_direction"] == "Hiring"
    assert fields["job_role"] == "cashier"
    assert fields["public_phone"] == "+9607844422"
    assert fields["job_salary_min_mvr"] == 5001
    assert fields["job_salary_max_mvr"] == 10000


def test_job_fields_for_section_only_enriches_jobs():
    from scanner.job_intelligence import job_fields_for_section
    item = {"title": "Cashier", "summary": "We are hiring a cashier. WhatsApp 7844422"}
    assert job_fields_for_section("Jobs", item)["job_direction"] == "Hiring"
    assert job_fields_for_section("Mobile Phones", item) is None
