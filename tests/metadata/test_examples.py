# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Test example metadata check rules."""

from invenio_checks.metadata import MetadataCheck

OPEN_ACCESS_RULE = {
    "id": "open-access-publication",
    "title": "Open Access Publication",
    "message": "Publication articles must be Open Access",
    "description": "The EU curation policy requires publication articles must be Open Access",
    "level": "failure",
    "condition": {
        "type": "comparison",
        "left": {"type": "field", "path": "metadata.resource_type.id"},
        "operator": "==",
        "right": "publication-article",
    },
    "checks": [
        {
            "type": "comparison",
            "left": {"type": "field", "path": "access.files"},
            "operator": "==",
            "right": "public",
        }
    ],
}

JOURNAL_INFO_RULE = {
    "id": "journal-info",
    "title": "Journal Information",
    "message": "Publication articles must state the journal it was published in",
    "description": "The EU curation policy requires publication articles must state the journal it was published in",
    "level": "failure",
    "condition": {
        "type": "comparison",
        "left": {"type": "field", "path": "metadata.resource_type.id"},
        "operator": "==",
        "right": "publication-article",
    },
    "checks": [
        {
            "type": "comparison",
            "left": {
                "type": "field",
                "path": "custom_fields.journal:journal.title",
            },
            "operator": "!=",
            "right": "",
        }
    ],
}

LICENSE_RULE = {
    "id": "license",
    "title": "License",
    "message": "All records must have a license",
    "description": "The EU curation policy requires all records to have a license",
    "level": "failure",
    "checks": [
        {
            "type": "list",
            "operator": "exists",
            "path": "metadata.rights",
            "predicate": {},
        }
    ],
}

SOFTWARE_LICENSE_RULE = {
    "id": "software-license",
    "title": "Software License",
    "message": "Software must have an appropriate license",
    "description": "The EU curation policy requires software to have an appropriate license",
    "level": "warning",
    "condition": {
        "type": "logical",
        "operator": "and",
        "expressions": [
            {
                "type": "comparison",
                "left": {"type": "field", "path": "metadata.resource_type.id"},
                "operator": "==",
                "right": "software",
            },
            {
                "type": "comparison",
                "left": {"type": "field", "path": "access.files"},
                "operator": "==",
                "right": "public",
            },
        ],
    },
    "checks": [
        {
            "type": "comparison",
            "left": {"type": "field", "path": "metadata.rights"},
            "operator": "==",
            "right": "",
        }
    ],
}

EU_FUNDING_RULE = {
    "id": "eu-funding",
    "title": "EU Funding",
    "message": "Records must have at least one EU-funded project",
    "description": "The EU curation policy requires author to have persistent identifiers",
    "level": "info",
    "checks": [
        {
            "type": "list",
            "operator": "any",
            "path": "metadata.funding",
            "predicate": {
                "type": "comparison",
                "left": {"type": "field", "path": "funder.id"},
                "operator": "==",
                "right": "00k4n6c32",
            },
        }
    ],
}

CREATOR_IDENTIFIERS_RULE = {
    "id": "creator-identifiers",
    "title": "Creator Identifiers",
    "message": "All creators must have at least one identifier",
    "level": "warning",
    "checks": [
        {
            "type": "list",
            "operator": "all",
            "path": "metadata.creators",
            "predicate": {
                "type": "logical",
                "operator": "and",
                "expressions": [
                    {"type": "field", "path": "person_or_org.identifiers"},
                    {
                        "type": "list",
                        "operator": "any",
                        "path": "person_or_org.identifiers",
                        "predicate": {"type": "field", "path": "identifier"},
                    },
                ],
            },
        }
    ],
}

AFFILIATION_IDENTIFIERS_RULE = {
    "id": "affiliation-identifiers",
    "title": "Affiliation Identifiers",
    "message": "All creator affiliations must have IDs",
    "level": "warning",
    "checks": [
        {
            "type": "list",
            "operator": "all",
            "path": "metadata.creators",
            "predicate": {
                "type": "list",
                "operator": "all",
                "list_path": "affiliations",
                "predicate": {"type": "field", "path": "id"},
            },
        }
    ],
}

ALL_RULES = [
    OPEN_ACCESS_RULE,
    JOURNAL_INFO_RULE,
    LICENSE_RULE,
    SOFTWARE_LICENSE_RULE,
    EU_FUNDING_RULE,
    CREATOR_IDENTIFIERS_RULE,
    AFFILIATION_IDENTIFIERS_RULE,
]


def test_full_example():
    """Test full example."""
    minimal_record = {}
    full_record = {
        "metadata": {
            "resource_type": {"id": "publication-article"},
            "title": "A full example",
            "creators": [
                {
                    "person_or_org": {
                        "name": "Ioannidis, Alex",
                        "identifiers": [{"identifier": "0000-0002-5082-6404"}],
                    },
                    "affiliations": [{"name": "CERN", "id": "03yrm5c26"}],
                }
            ],
            "funding": [
                {"funder": {"id": "00k4n6c32"}, "award": {"id": "00k4n6c32::1234"}}
            ],
            "rights": [{"id": "MIT", "props": {"osi_approved": "y"}}],
        },
        "access": {"files": "public"},
        "custom_fields": {
            "journal:journal": {"title": "A full example"},
        },
    }

    # Create a check instance
    check = MetadataCheck()

    # Test minimal record against all rules
    min_result = check.run(
        minimal_record, {"rules": ALL_RULES}, community="test_community"
    )

    # Test full record against all rules
    full_result = check.run(
        full_record, {"rules": ALL_RULES}, community="test_community"
    )

    # Verify results
    assert len(min_result.rule_results) == len(
        ALL_RULES
    ), "All rules should produce a result for minimal record"
    assert len(full_result.rule_results) == len(
        ALL_RULES
    ), "All rules should produce a result for full record"

    # Minimal record should fail most checks
    failed_min = [r for r in min_result.rule_results if not r.success]
    assert len(failed_min) > 0, "Minimal record should fail some checks"

    # Full record should pass at least some checks
    passed_full = [r for r in full_result.rule_results if r.success]
    assert len(passed_full) > 0, "Full record should pass some checks"


def test_individual_rules():
    """Test each rule individually to verify their behavior."""
    # Test individual rules against appropriate records

    # 1. Test open access rule
    publication_record = {
        "metadata": {"resource_type": {"id": "publication-article"}},
        "access": {"files": "public"},
    }
    check = MetadataCheck()
    result = check.run(
        publication_record, {"rules": [OPEN_ACCESS_RULE]}, community="test_community"
    )
    assert result.rule_results[
        0
    ].success, "Open access rule should pass for public publication"

    # Test failure case
    restricted_pub = {
        "metadata": {"resource_type": {"id": "publication-article"}},
        "access": {"files": "restricted"},
    }
    result = check.run(
        restricted_pub, {"rules": [OPEN_ACCESS_RULE]}, community="test_community"
    )
    assert not result.rule_results[
        0
    ].success, "Open access rule should fail for restricted publication"

    # 2. Test journal info rule
    journal_record = {
        "metadata": {"resource_type": {"id": "publication-article"}},
        "custom_fields": {"journal:journal": {"title": "Example Journal"}},
    }
    result = check.run(
        journal_record, {"rules": [JOURNAL_INFO_RULE]}, community="test_community"
    )
    assert result.rule_results[
        0
    ].success, "Journal info rule should pass with journal title"

    # Test failure case
    no_journal = {
        "metadata": {"resource_type": {"id": "publication-article"}},
        "custom_fields": {"journal:journal": {"title": ""}},
    }
    result = check.run(
        no_journal, {"rules": [JOURNAL_INFO_RULE]}, community="test_community"
    )
    assert not result.rule_results[
        0
    ].success, "Journal info rule should fail with empty journal title"

    # 3. Test license rule
    license_record = {"metadata": {"rights": [{"id": "CC-BY-4.0"}]}}
    result = check.run(
        license_record, {"rules": [LICENSE_RULE]}, community="test_community"
    )
    assert result.rule_results[0].success, "License rule should pass with rights field"

    # Test failure case
    no_license = {}
    result = check.run(
        no_license, {"rules": [LICENSE_RULE]}, community="test_community"
    )
    assert not result.rule_results[
        0
    ].success, "License rule should fail without rights field"

    # 4. Test software license rule
    software_record = {
        "metadata": {"resource_type": {"id": "software"}, "rights": "MIT"},
        "access": {"files": "public"},
    }
    result = check.run(
        software_record, {"rules": [SOFTWARE_LICENSE_RULE]}, community="test_community"
    )
    assert not result.rule_results[
        0
    ].success, "Software license rule should fail with wrong rights format"

    # 5. Test EU funding rule
    funding_record = {"metadata": {"funding": [{"funder": {"id": "00k4n6c32"}}]}}
    result = check.run(
        funding_record, {"rules": [EU_FUNDING_RULE]}, community="test_community"
    )
    assert result.rule_results[
        0
    ].success, "EU funding rule should pass with EU funder ID"

    # Test failure case
    other_funding = {"metadata": {"funding": [{"funder": {"id": "different-id"}}]}}
    result = check.run(
        other_funding, {"rules": [EU_FUNDING_RULE]}, community="test_community"
    )
    assert not result.rule_results[
        0
    ].success, "EU funding rule should fail with non-EU funder ID"

    # 6. Test creator identifiers rule
    creator_record = {
        "metadata": {
            "creators": [
                {
                    "person_or_org": {
                        "name": "Smith, John",
                        "identifiers": [{"identifier": "0000-0001-1234-5678"}],
                    }
                }
            ]
        }
    }
    result = check.run(
        creator_record,
        {"rules": [CREATOR_IDENTIFIERS_RULE]},
        community="test_community",
    )
    assert result.rule_results[
        0
    ].success, "Creator identifiers rule should pass with identifiers"

    # 7. Test affiliation identifiers rule
    affiliation_record = {
        "metadata": {
            "creators": [
                {
                    "person_or_org": {"name": "Smith, John"},
                    "affiliations": [{"name": "CERN", "id": "03yrm5c26"}],
                }
            ]
        }
    }
    result = check.run(
        affiliation_record,
        {"rules": [AFFILIATION_IDENTIFIERS_RULE]},
        community="test_community",
    )
    assert result.rule_results[
        0
    ].success, "Affiliation identifiers rule should pass with affiliation IDs"

    # Test failure case
    no_aff_id = {
        "metadata": {
            "creators": [
                {
                    "person_or_org": {"name": "Smith, John"},
                    "affiliations": [{"name": "CERN"}],  # Missing ID
                }
            ]
        }
    }
    result = check.run(
        no_aff_id, {"rules": [AFFILIATION_IDENTIFIERS_RULE]}, community="test_community"
    )
    assert not result.rule_results[
        0
    ].success, "Affiliation identifiers rule should fail without affiliation IDs"


def test_complex_record():
    """Test a complex record against all rules."""
    complex_record = {
        "metadata": {
            "resource_type": {"id": "publication-article"},
            "title": "Complex example with multiple features",
            "creators": [
                {
                    "person_or_org": {
                        "name": "Ioannidis, Alex",
                        "identifiers": [{"identifier": "0000-0002-5082-6404"}],
                    },
                    "affiliations": [{"name": "CERN", "id": "03yrm5c26"}],
                },
                {
                    "person_or_org": {
                        "name": "Smith, John",
                        "identifiers": [{"identifier": "0000-0001-9876-5432"}],
                    },
                    "affiliations": [{"name": "University", "id": "03abcdef"}],
                },
            ],
            "funding": [
                {"funder": {"id": "00k4n6c32"}, "award": {"id": "00k4n6c32::1234"}},
                {"funder": {"id": "other-funder"}, "award": {"id": "other-award"}},
            ],
            "rights": [
                {"id": "CC-BY-4.0"},
                {"id": "MIT", "props": {"osi_approved": "y"}},
            ],
        },
        "access": {"files": "public"},
        "custom_fields": {
            "journal:journal": {"title": "Scientific Journal of Examples"},
        },
    }

    check = MetadataCheck()
    results = check.run(
        complex_record, {"rules": ALL_RULES}, community="test_community"
    )

    # Get rule results by ID for easier assertions
    result_by_id = {r.rule_id: r for r in results.rule_results}

    # Check that all the expected rules were evaluated
    for rule in ALL_RULES:
        assert rule["id"] in result_by_id, f"Rule {rule['id']} not found in results"

    # Complex record should pass all relevant checks
    assert result_by_id[
        "open-access-publication"
    ].success, "Should pass open access check"
    assert result_by_id["journal-info"].success, "Should pass journal info check"
    assert result_by_id["license"].success, "Should pass license check"
    # Software license not applicable since not a software record
    assert result_by_id["eu-funding"].success, "Should pass EU funding check"
    assert result_by_id[
        "creator-identifiers"
    ].success, "Should pass creator identifiers check"
    assert result_by_id[
        "affiliation-identifiers"
    ].success, "Should pass affiliation IDs check"
