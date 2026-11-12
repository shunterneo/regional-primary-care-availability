"""Fail-closed public-evidence display policy for ongoing-care intake.

A web-page review confirms a published application pathway, NOT roster space or
telephone verification. Metadata must be explicit: old imported labels never
acquire first-party verification merely because a page is fetched or rebuilt.
"""
from __future__ import annotations
from datetime import date
from urllib.parse import urlsplit

MAX_PUBLIC_EVIDENCE_AGE_DAYS=21


def host(url):
    try:
        return (urlsplit(url or '').hostname or '').lower().removeprefix('www.')
    except (TypeError,ValueError):
        return ''


def qualified_public_intake(clinic, today):
    """True only for recent location/physician-specific first-party ongoing-care notices."""
    v=clinic.get('intake_verification') or {}
    if clinic.get('intake_conflict'):
        return False
    if clinic.get('status')!='accepting' or clinic.get('care_model') not in ('ongoing','both'):
        return False
    if clinic.get('operating_status') in ('closed','archived'):
        return False
    if v.get('tier')!='clinic_first_party' or v.get('scope') not in ('location','named_clinician'):
        return False
    if v.get('method') not in ('public_webpage_review','two_day_official_monitor','reviewer_verified_public_source'):
        return False
    if not v.get('finding') or not v.get('source_url') or v.get('source_url')!=clinic.get('evidence_url'):
        return False
    if not host(v['source_url']) or host(v['source_url'])!=host(clinic.get('clinic_url')):
        return False
    try:
        age=(today-date.fromisoformat(v['reviewed_on'])).days
    except (TypeError,ValueError,KeyError):
        return False
    return 0<=age<=MAX_PUBLIC_EVIDENCE_AGE_DAYS


def display_intake_status(clinic, today):
    """No green from a third-party, program-wide, stale, or missing evidence record."""
    status=clinic.get('status','unknown')
    if status=='accepting':
        if qualified_public_intake(clinic,today):return 'accepting'
        v=clinic.get('intake_verification') or {}
        if v.get('tier') in ('third_party','authoritative_secondary','program_general'):
            return 'reported'
        return 'needs_review'
    if status=='unknown':return 'unknown'
    # Other classifications retain their distinct non-green meaning; stale claims are flagged.
    try:
        age=(today-date.fromisoformat(clinic['last_reviewed'])).days
    except (TypeError,ValueError,KeyError):return 'needs_review'
    if age<0 or age>(45 if status in ('reported','waitlist') else 30):return 'needs_review'
    return status


def verification_display(clinic):
    v=clinic.get('intake_verification') or {}
    tier=v.get('tier','unverified')
    if clinic.get('status')=='unknown' and tier in ('clinic_first_party','program_general'):
        return 'Public clinic source reviewed; current intake not confirmed'
    return {
        'clinic_first_party':'Clinic-published intake evidence (public-source review only)',
        'program_general':'Program-wide notice; this location not individually confirmed',
        'authoritative_secondary':'Official third-party announcement; clinic confirmation outstanding',
        'third_party':'Third-party directory report; direct clinic verification outstanding',
        'conflicting_or_unconfirmed':'Conflicting, future or insufficient intake information',
        'unverified':'No current individual intake evidence recorded',
    }.get(tier,'Evidence level not verified')
