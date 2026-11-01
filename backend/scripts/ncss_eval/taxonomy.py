"""NCSS-aligned taxonomy for Schemes SG (Phase 1 draft, local only).

Source: NCSS Programme Taxonomy v1.1 (28 Oct 2026; annex labels are canonical) + "Mapping of NCSS & Schemes SG Taxos.xlsx".
Decision (issue #406): keep granular terms as the filter level; each term carries NCSS parent(s)
from this static table (never from the LLM).

Parents are lists because a term can roll up to an age group, a profile, both, or neither.
`provisional=True` = parent not yet confirmed by NCSS; `fallback` = parent to use if NCSS says no.
"""
from dataclasses import dataclass, field

AGE_GROUPS = {
    "Children": "12 years and below.",
    "Youths": "13 to 21 years inclusive.",
    "Adults": "22 to 59 years inclusive.",
    "Seniors": "60 years and above.",
}

PROFILES = {
    "Caregiver": "Individuals providing ongoing primary care and support to a person with care needs due to age, disability, illness or mental health conditions.",
    "Persons with disabilities": "Individuals with permanent intellectual or physical disabilities. Recoverable conditions such as mental health conditions are NOT disabilities.",
    "Persons with mental health conditions": "Individuals diagnosed with clinically recognised conditions or severe mental health challenges that impair daily functioning, well-being or social participation.",
    "Persons with financial difficulties": "Individuals or households without enough financial resources to meet basic living needs, e.g. affording food, housing, utilities, healthcare, or managing debt.",
    "Ex-offender": "Individuals previously convicted of an offence who have completed their sentence and are reintegrating into the community.",
    "Unemployed": "Individuals not in paid work, available for work, who may be seeking employment and support to re-enter the workforce.",
    "Chronically ill": "Individuals with long-term or persistent health conditions, or terminally ill, requiring ongoing management and whose daily functioning is impaired.",
    "Multi-stressed family": "Families facing multiple concurrent challenges across two or more needs (e.g. financial, mental health, employment) that need coordinated, holistic support.",
    "Persons with substance and behavioural addictions": "Individuals dependent on substances or compulsively engaged in behaviours (e.g. gambling) that impair health, functioning and social well-being and who need recovery support.",
    "Migrant individual": "Persons not native to Singapore who may face language, cultural or legal barriers to settling here, e.g. for employment or studies.",
    # Schemes SG extensions (NCSS 28 Oct): not in NCSS v1.1, kept distinct from NCSS categories (see EXTENSION_PROFILES).
    "Families": "Families in general, incl. preventive, parenting, marriage and family programmes not limited to multi-stressed families.",
    "Persons experiencing homelessness": "Persons without access to stable and safe accommodation, who may sleep in public spaces or move between temporary housing. (NCSS definition, xlsx Sheet3.)",
    "Victims of abuse or harassment": "Persons who have experienced abuse, family violence or harassment.",
}
EXTENSION_PROFILES = {"Families", "Persons experiencing homelessness", "Victims of abuse or harassment"}

NEEDS = [
    "Caregiving support", "Community participation/engagement", "Counselling and crisis support", "Education and learning",
    "Work and employment", "Financial and material support", "Fostering and alternative care", "Healthcare and well-being",
    "Home maintenance", "Housing and shelter support", "Intrapersonal challenges", "Retirement and legacy planning",
    "Justice and legal protection", "Family, parenting and relationships", "Mental health", "Disability support",
    "Personal development", "Recreational activities", "Reintegration/Transition services", "Social support",
    "Substance and behavioural addictions recovery",
]

INTERVENTIONS = [
    "Befriending", "Care services", "Casework/Case management", "Coaching", "Community development/outreach",
    "Counselling", "Crisis assessment and intervention", "Enrichment activities", "Financial/material assistance",
    "Group work", "Helpline/Hotline", "Shelter provision", "Home maintenance services", "Information and referral",
    "Information and communication accessibility", "Learning intervention", "Legal services",
    "Medical clinic and services", "Mentoring", "Mobility services", "Psychoeducation", "Therapy", "Training",
    "Transportation", "Tuition", "Job placement",
]


@dataclass(frozen=True)
class Term:
    name: str
    definition: str
    age_group: tuple = ()
    profile: tuple = ()
    provisional: bool = False
    fallback_profile: tuple = ()  # used if NCSS rejects a provisional parent
    note: str = ""


def T(name, definition, age=(), profile=(), provisional=False, fallback=(), note=""):
    return Term(name, definition, tuple(age), tuple(profile), provisional, tuple(fallback), note)


# ---------------------------------------------------------------- who_is_it_for
# 4 need-terms moved out (-> what_it_gives): Need shelter, Need food support, Need mortgage support,
# Individuals needing legal aid. Added: Adults, Multi-stressed families, Persons with substance and
# behavioural addictions. renamed Elderly -> Seniors (family) and mental health issues -> conditions on 2026-10-04 (user-approved Step 0); see RENAMES.
WHO_IS_IT_FOR = [
    T("Children", "Umbrella: children aged 12 and below (any child age band below also applies).", age=["Children"]),
    T("Infants and toddlers (0-3)", "Children aged 0 to 3 (infant care, early intervention, toddlers).", age=["Children"], note="granular: CareCompass"),
    T("Preschool children (4-6)", "Children aged 4 to 6 (kindergarten, preschool).", age=["Children"], note="granular: CareCompass"),
    T("Primary school children (7-12)", "Children aged 7 to 12 (primary school).", age=["Children"], note="granular: CareCompass"),
    T("Teenagers (13-17)", "Adolescents aged 13 to 17 (secondary school / minors).", age=["Youths"], note="granular: CareCompass; under-18"),
    T("Youth", "Umbrella: youths aged 13 to 21.", age=["Youths"]),
    T("Youth-at-risk", "Youths aged 13 to 21 at risk of offending, school dropout, or other adverse outcomes.", age=["Youths"]),
    T("Teenagers facing pregnancy", "Teenagers (13-19) who are pregnant or facing an unplanned pregnancy.", age=["Youths"]),
    T("Young adults", "Persons aged roughly 18-35. NCSS does not use this band; use only if the scheme says 'young adults'.", age=["Youths", "Adults"], note="NCSS: no consistent age range"),
    T("Adults", "Adults aged 22 to 59.", age=["Adults"]),
    T("Students", "Persons currently enrolled in school/tertiary education. Education status, not a social-service population.", note="NCSS: eligibility metadata"),
    T("Families", "Families in general, not necessarily in distress.", profile=["Families"]),
    T("Multi-stressed families", "Families facing multiple concurrent challenges across two or more needs.", profile=["Multi-stressed family"]),
    T("Single parents", "Parents raising children on their own (divorced, widowed, unmarried, separated).", profile=["Families"]),
    T("Women", "Programme restricted to women. Demographic marker.", note="NCSS: metadata, no profile"),
    T("Pregnant individuals in distress", "Pregnant persons facing crisis, unplanned pregnancy or hardship.", note="NCSS: circumstance; no profile"),
    T("Seniors", "Seniors / elderly persons aged 60 and above (formerly 'Elderly').", age=["Seniors"]),
    T("Seniors with dementia", "Seniors / elderly persons aged 60+ diagnosed with dementia, and their care.", age=["Seniors"], profile=["Chronically ill"]),
    T("Persons with disabilities (PWDs)", "Persons with permanent intellectual or physical disabilities (e.g. mobility, vision, hearing, intellectual disability, cerebral palsy). Mental health conditions are NOT disabilities.", profile=["Persons with disabilities"]),
    T("Persons with special needs", "Persons with developmental or learning needs (e.g. SPED students). Tag Persons with disabilities (PWDs) separately only when the disability is permanent.", note="NCSS 14 Oct row 11: do not equate with PWD; no PWD parent"),
    T("Persons on autism spectrum", "Persons diagnosed with autism spectrum disorder.", profile=["Persons with disabilities"]),
    T("Persons with chronic or terminal illnesses", "Persons with long-term, persistent or terminal illness requiring ongoing management (e.g. cancer, kidney failure, diabetes).", profile=["Chronically ill"]),
    T("Persons with mental health conditions", "Persons diagnosed with, or severely affected by, mental health conditions (e.g. depression, schizophrenia). Recoverable, so NOT persons with disabilities.", profile=["Persons with mental health conditions"]),
    T("Persons with substance and behavioural addictions", "Persons dependent on substances or compulsive behaviours (drugs, alcohol, gambling, gaming).", profile=["Persons with substance and behavioural addictions"]),
    T("Individuals with gambling addiction", "Persons with a gambling addiction or problem gambling, and affected family.", profile=["Persons with substance and behavioural addictions"]),
    T("Caregivers", "People providing ongoing primary care to someone with care needs from age, disability, illness or mental health condition.", profile=["Caregiver"], note="check vs NCSS Caregiver def"),
    T("Low income", "Individuals/households with insufficient income, incl. those on means-tested schemes.", profile=["Persons with financial difficulties"]),
    T("Low income families", "Families with low household income.", profile=["Persons with financial difficulties", "Families"]),
    T("Low income seniors", "Seniors / elderly persons aged 60+ with low income.", age=["Seniors"], profile=["Persons with financial difficulties"]),
    T("Facing financial hardship", "Persons or households in temporary or acute financial difficulty (job loss, debt, emergencies).", profile=["Persons with financial difficulties"]),
    T("Unemployed", "Persons not in paid work, available for and seeking work.", profile=["Unemployed"]),
    T("Retrenched", "Persons who lost their job through retrenchment.", profile=["Unemployed"]),
    T("Homeless", "Persons without stable, safe accommodation, sleeping rough or moving between temporary housing.", profile=["Persons experiencing homelessness"], note="NCSS 5 Oct: creates parent profile Persons Experiencing Homelessness"),
    T("Foreign domestic workers/maids", "Foreign domestic workers (maids) employed in Singapore households, and their employers when the scheme is for FDW matters.", profile=["Migrant individual"]),
    T("Migrant workers/Foreign workers", "Foreign workers in Singapore on work passes (e.g. construction, marine).", profile=["Migrant individual"]),
    T("Transnational families/Foreign spouses", "Foreign spouses of Singaporeans and cross-border families.", profile=["Migrant individual", "Families"]),
    T("Ex-offenders", "Persons who completed a sentence and are reintegrating.", profile=["Ex-offender"]),
    T("Inmates", "Persons currently in prison or custody.", provisional=True, note="NCSS 5 Oct: keep as profile, no parent until NCSS names one"),
    T("Families of inmates or ex-offenders", "Family members of inmates or ex-offenders.", profile=["Families"]),
    T("Victims of abuse or harassment", "Persons experiencing or who experienced abuse, family violence, or harassment.", profile=["Victims of abuse or harassment"], provisional=True, fallback=["Multi-stressed family"], note="NCSS 5 Oct: a need, not a profile; 14 Oct Q6.1 our proposal: keep here + need Protection from Violence"),
    T("Facing end of life", "Persons with a life-limiting illness nearing end of life, and their families.", note="NCSS: circumstance; review under needs, no profile parent until needs mapping arrives"),
    T("Individuals struggling with loss", "Persons bereaved or grieving. Circumstance, not a population.", note="NCSS: review under needs; no profile parent"),
    T("Malay/Muslim community", "Programme targeted at Malay/Muslim community. Demographic marker.", note="NCSS: metadata"),
    T("Indian community", "Programme targeted at Indian community. Demographic marker.", note="NCSS: metadata"),
    T("Chinese community", "Programme targeted at Chinese community. Demographic marker.", note="NCSS: metadata"),
    T("General public", "Open to all residents with no specific target group. Use ONLY if no other term fits.", note="NCSS: access descriptor"),
]
# NB: Gap check vs constants.py (43): -4 moved need terms +3 added = 42 here? count asserted in tests.

# ---------------------------------------------------------------- what_it_gives
def G(name, definition, *interventions, provisional=False, note=""):
    # 'profile' slot reused = intervention parents
    return Term(name, definition, (), tuple(interventions), provisional, (), note)


WHAT_IT_GIVES = [
    G("Counselling", "Professional guidance by trained counsellors for personal or family issues.", "Counselling"),
    G("Casework", "Coordinated assessment, planning and monitoring of a person's needs by a social worker.", "Casework/Case management"),
    G("Emotional care", "Non-clinical emotional support and companionship (listening, befriending, comfort). Skip if Counselling or Befriending services already describe the same service.", "Befriending", "Counselling", provisional=True, note="NCSS: no match, programme review pending"),
    G("Mental health assessment and treatment", "Clinical assessment/treatment of mental health conditions by clinicians.", "Therapy", "Medical clinic and services", provisional=True, note="NCSS: no match, programme review pending"),
    G("Psychological support/Psychotherapy", "Only when psychologists/psychotherapists or psychological therapy are explicitly offered. General counselling is Counselling, not this.", "Therapy"),
    G("Befriending services", "Regular companionship to reduce isolation.", "Befriending"),
    G("Helpline services", "Phone/digital helpline support.", "Helpline/Hotline"),
    G("Information and referral services", "Information, guidance or referral/signposting to other services as a main function of the scheme (not just a passing mention).", "Information and referral"),
    G("Educational programmes", "Structured teaching of knowledge or awareness (courses, workshops, talks, parent education) as a main component. Not for counselling or support services that merely include some sessions.", "Psychoeducation", "Training", provisional=True, note="NCSS: review programmes to find actual intervention"),
    G("Learning intervention", "Targeted, structured educational or developmental support for learning or developmental difficulties (e.g. early intervention, educational therapy, learning support, literacy/numeracy intervention). Use Tuition for school-subject tuition.", "Learning intervention", note="NCSS v1.1 definition (incl. early intervention)"),
    G("Vocational training", "Skills training for employment.", "Training"),
    G("Employment assistance", "Job search help, placement, job coaching or employer matching. Skills courses are Vocational training instead.", "Job placement", "Coaching"),
    G("Skills training and job matching", "Skills upgrading with job placement.", "Training", "Job placement"),
    G("Financial assistance (general)", "Cash or in-kind help NOT tied to one stated purpose. If the funds are for a stated purpose (education, healthcare, housing, daily living, etc.) use that specific term INSTEAD of this one.", "Financial/material assistance"),
    G("Financial assistance for daily living expenses", "Help with everyday living costs.", "Financial/material assistance"),
    G("Financial assistance for healthcare", "Help paying medical bills or care.", "Financial/material assistance"),
    G("Financial assistance for chronic or terminal illnesses", "Funding for long-term/terminal illness care.", "Financial/material assistance"),
    G("Financial assistance for education", "Bursaries, fee or school-cost help.", "Financial/material assistance"),
    G("Financial assistance for kindergarten/student care", "Subsidies for preschool/student care.", "Financial/material assistance"),
    G("Financial assistance for assistive technology and medical equipment", "Funding for assistive devices/equipment.", "Financial/material assistance"),
    G("Financial assistance for housing", "Help with rent, housing costs.", "Financial/material assistance"),
    G("Mortgage assistance", "Help paying home loans.", "Financial/material assistance"),
    G("Debt assistance", "Help managing or repaying debt.", "Casework/Case management"),
    G("Burial and emergency assistance", "Funeral or emergency cash aid.", "Financial/material assistance", provisional=True, note="NCSS: no match, programme review pending"),
    G("Food support", "Food distribution, vouchers, meals.", "Financial/material assistance"),
    G("Housing/Shelter", "Temporary or transitional shelter or housing help.", "Shelter provision"),
    G("Respite care", "Temporary relief care so that a caregiver can rest. Not for general caregiver training or support (caregiver support is a service user need, not an intervention).", "Care services"),
    G("Senior sitting and caregiving services", "Home or centre sitting/caregiving for seniors / the elderly.", "Care services"),
    G("Childcare services", "Care for children while parents are away.", "Care services"),
    G("Babysitting/Childcare services", "Babysitting and childcare.", "Care services"),
    G("Student care", "After-school care.", "Care services"),
    G("Tuition", "Academic tuition and homework/learning coaching for school subjects.", "Tuition"),
    G("Enrichment programmes", "Non-academic enrichment (arts, sports, life skills, holiday programmes) for personal growth.", "Enrichment activities", provisional=True, note="NCSS: no match, review programmes"),
    G("Transport subsidies", "Subsidised fares/transport.", "Financial/material assistance"),
    G("Medical transport assistance", "Transport to medical appointments.", "Transportation"),
    G("Healthcare (general/basic services)", "General clinic and basic health services.", "Medical clinic and services"),
    G("Dental services", "Dental care.", "Medical clinic and services"),
    G("Traditional Chinese Medicine (TCM)", "TCM clinics and services.", "Medical clinic and services"),
    G("Rehabilitation services (Physiotherapy/Occupational therapy)", "Physio/occupational rehabilitation.", "Therapy"),
    G("Legal aid and services", "Legal advice, aid and representation.", "Legal services"),
    G("Residential care/programmes", "Live-in care or programmes.", "Care services"),
    G("Addictions treatment and rehabilitation", "Treatment and recovery support for addictions.", "Therapy", "Group work", provisional=True, note="NCSS: no match, programme review pending"),
    G("Social and recreational activities", "Group social, recreational, exercise, arts or outing activities for engagement and connection, when such activities are a main component.", "Enrichment activities", "Group work"),
    G("Support groups", "Facilitated peer or group support.", "Group work"),
    G("Bereavement support", "Support for grief and loss.", "Counselling", "Group work", provisional=True, note="NCSS: no match, programme review pending"),
    G("End-of-life care", "Palliative and end-of-life care.", "Care services", "Medical clinic and services", provisional=True, note="NCSS: no match, programme review pending"),
    G("Subsidies for Foreign Domestic Workers (FDWs)", "Subsidies for hiring/training FDWs.", "Financial/material assistance"),
    G("Retirement and financial planning assistance", "Advice on retirement/financial planning.", "Information and referral", "Coaching", provisional=True, note="NCSS: no match, programme review pending"),
    G("Benefits and perks for PWDs (transport, discounts, facilities)", "Concessions for persons with disabilities.", "Financial/material assistance"),
    G("Technology assistance (internet/computers)", "Devices, internet access, digital help.", "Financial/material assistance"),
    G("Home retrofitting", "Home modifications, repairs and upgrades (e.g. grab bars, ramps, minor repairs).", "Home maintenance services", provisional=True, note="NCSS: conditional match, review programmes"),
    G("Assistive technology", "Assistive devices and equipment (e.g. mobility aids, hearing aids, wheelchairs).", "Mobility services", provisional=True, note="our assumption; NCSS has no match"),
    G("Funding for community projects", "Grants for community initiatives.", "Community development/outreach"),
]

# ---------------------------------------------------------------- scheme_type (need domains only)
# Population terms removed (15). Parent = NCSS Service User Need(s).
def N(name, definition, *needs, provisional=False, note=""):
    return Term(name, definition, (), tuple(needs), provisional, (), note)


SCHEME_TYPE = [
    N("Family and Parenting Support", "Parenting, marriage, family relationship and family life support.", "Family, parenting and relationships"),
    N("Disability Support", "Support for persons with disabilities: mobility, daily living, centre/home-based care, accessibility.", "Disability support"),
    N("Active Ageing and Social Activities", "Social, recreational and active-ageing activities that keep seniors (or others) engaged and connected.", "Recreational activities", "Social support"),
    # NCSS 28 Oct: Child and Youth Services split in three, one need each. A scheme can take more than one.
    N("Fostering and alternative care", "Foster care, adoption, kinship care and children's homes for children who cannot live with their own family. Child protection is Protection from Violence.", "Fostering and alternative care"),
    N("Youth development", "Personal growth of children and youths: mentoring, leadership, youth centres, life skills and enrichment. Tuition and learning support are Education Support.", "Personal development"),
    N("Child and youth emotional support", "Counselling, emotional regulation and coping support for children and youths, incl. youth at risk.", "Intrapersonal challenges"),
    N("Caregiver Support", "Training, respite and support for caregivers.", "Caregiving support"),
    N("Ex-offender Support", "Reintegration support for ex-offenders.", "Reintegration/Transition services"),
    N("Education Support", "Tuition, learning support, school-related help.", "Education and learning"),
    N("Student Care Support", "After-school and student care. Some programmes also meet educational needs (NCSS: review at programme level).", "Caregiving support"),
    N("Healthcare", "Treatment and prevention of physical health issues.", "Healthcare and well-being"),
    N("Dental Healthcare", "Dental care.", "Healthcare and well-being"),
    N("General Healthcare Subsidies", "Subsidies for medical costs. Granular need: Healthcare support under Financial and material support.", "Financial and material support"),
    N("Chronic or Terminal Illness Support", "Support for long-term/terminal illness.", "Healthcare and well-being"),
    N("Mental Health", "Emotional support, treatment and rehabilitation for mental health conditions (rehabilitation is an intervention approach, not a separate need).", "Mental health"),
    N("End-of-Life/Palliative Care", "Palliative and end-of-life care.", "Healthcare and well-being"),
    N("Food Support", "Food and meals.", "Financial and material support"),
    N("Housing/Shelter", "Shelter and housing.", "Housing and shelter support"),
    N("Employment Support", "Help finding and keeping work.", "Work and employment"),
    N("Financial Assistance", "Cash or material aid.", "Financial and material support"),
    N("Debt Assistance", "Debt management.", "Financial and material support"),
    N("Financial Planning and Retirement Support", "Retirement and financial planning.", "Retirement and legacy planning"),
    N("Transport Support", "Transport help.", "Disability support", "Financial and material support", provisional=True, note="NCSS 14 Oct: no matching need; parents are our fallback"),
    N("Technology Support", "Digital access and assistive tech.", "Disability support", "Education and learning", provisional=True, note="NCSS 14 Oct: no matching need; parents are our fallback"),
    N("Protection from Violence", "Protection against violence.", "Justice and legal protection"),
    N("Community Funding", "Funding for community projects.", "Community participation/engagement", provisional=True, note="NCSS 14 Oct: may be a funder mechanism, not a need"),
    N("Addictions Rehabilitation", "Addiction recovery.", "Substance and behavioural addictions recovery"),
]

REMOVED_FROM_SCHEME_TYPE = [
    "Low Income", "Family", "Children", "Youth", "Youth-at-Risk", "Women", "Single Parents", "Elderly",
    "Persons with Disabilities (PWD)", "Special Needs", "Foreign Domestic Workers (FDWs)",
    "Migrant Workers/Foreign Workers", "Foreign Spouse/Transnational Family Support",
    "Incarcerated/Inmate Family Support", "General Public Support",
]
REMOVED_FROM_SCHEME_TYPE_2026_10_14 = [  # NCSS 14 Oct mapping sheet; meaning moves per LEGACY_ALIASES["scheme_type"]
    "Homelessness Support", "Vocational Training", "Legal Aid", "Residential Care", "Counselling and Emotional Support",
    "Traditional Chinese Medicine (TCM)", "Referral and Information Services", "Seniors Housing and Home Improvement",
    "COVID-19 Support", "Abuse/Family Violence", "Loss of Breadwinner Support",
]
REMOVED_FROM_SCHEME_TYPE_2026_10_28 = ["Child and Youth Services"]  # NCSS 28 Oct split; programmes re-tagged per scheme
MOVED_OUT_OF_WHO = {  # who term -> what_it_gives term
    "Need shelter": "Housing/Shelter", "Need food support": "Food support",
    "Need mortgage support": "Mortgage assistance", "Individuals needing legal aid": "Legal aid and services",
}

RENAMES = {  # old term -> new term (2026-10-04, Step 0). Used to map old gold/prod tags and as the migration alias seed.
    "Elderly": "Seniors", **{'Elderly with dementia': 'Seniors with dementia', 'Low income elderly': 'Low income seniors', 'Elder sitting and caregiving services': 'Senior sitting and caregiving services', 'Persons with mental health issues': 'Persons with mental health conditions'},
}
MOVED_OUT_NEED_PARENT = {  # moved who term -> NCSS Service User Need parent (NCSS 1 Oct email)
    "Need shelter": "Housing and shelter support", "Need food support": "Financial and material support",
    "Need mortgage support": "Financial and material support", "Individuals needing legal aid": "Justice and legal protection",
}
# Moved out of what_it_gives (describe a need / programme class, not an intervention). scheme_type already has the need.
REMOVED_FROM_WHAT_IT_GIVES = {
    "Protection against violence": "scheme_type: Protection from Violence",
    "Child protection services": "scheme_type: Protection from Violence",
    "Identification and safety tagging": "removed: no programme tagged (confirm count in prod)",
    "COVID-19 support": "removed: re-tag programmes by intervention delivered (R5)",
    "Referral services": "merged -> Information and referral services",
    "Information services": "merged -> Information and referral services",
    "Tuition/Enrichment programmes": "split -> Tuition + Enrichment programmes",
    "Home retrofitting and assistive technology": "split -> Home retrofitting + Assistive technology",
}
# NCSS intervention parents NCSS marked "no match, review programmes" (terms rolling up to them are provisional).
PROVISIONAL_INTERVENTION_PARENTS = {
    "Coaching", "Community development/outreach", "Crisis assessment and intervention", "Enrichment activities",
    "Mobility services", "Psychoeducation", "Mentoring", "Information and communication accessibility",
}


# ---------------------------------------------------------------- age bands (applied in CODE from age_min/age_max)
# Rule (user, 2026-09-29): tag EVERY band the stated range overlaps. Open-ended max = no upper bound.
AGE_BAND_TERMS = [  # (term, lo, hi)
    ("Infants and toddlers (0-3)", 0, 3), ("Preschool children (4-6)", 4, 6),
    ("Primary school children (7-12)", 7, 12), ("Children", 0, 12),
    ("Teenagers (13-17)", 13, 17), ("Youth", 13, 21),
    ("Adults", 22, 59), ("Seniors", 60, 200),
]
AGE_TERM_NAMES = {t for t, _, _ in AGE_BAND_TERMS}


def age_terms(age_min, age_max):
    """Terms whose band overlaps [age_min, age_max]; None bounds are open. Returns None if no age given."""
    if age_min is None and age_max is None:
        return None
    lo = 0 if age_min is None else age_min
    hi = 200 if age_max is None else age_max
    return {t for t, a, b in AGE_BAND_TERMS if lo <= b and hi >= a}


# ---------------------------------------------------------------- frontend category mapping (10 categories kept)
# Old mapping used population terms in scheme_type (removed). v2 is built from need-domain terms only.
# Firestore array-contains-any allows <=30 values per query: keep each list well under that.
SCHEME_CATEGORY_MAPPING_V2 = {
    "Financial Assistance": ["Financial Assistance", "Debt Assistance", "Financial Planning and Retirement Support"],
    "Family & Children": ["Family and Parenting Support", "Fostering and alternative care", "Youth development",
                          "Child and youth emotional support"],
    "Health & Wellbeing": ["Healthcare", "Dental Healthcare", "General Healthcare Subsidies",
                           "Chronic or Terminal Illness Support", "Mental Health",
                           "End-of-Life/Palliative Care", "Addictions Rehabilitation"],
    "Housing & Food": ["Housing/Shelter", "Food Support"],
    "Education": ["Education Support", "Student Care Support"],
    "Employment & Training": ["Employment Support", "Ex-offender Support"],
    "Seniors & Caregiving": ["Caregiver Support", "Active Ageing and Social Activities"],
    "Disability & Transport": ["Disability Support", "Transport Support", "Technology Support"],
    "Legal & Safety": ["Protection from Violence"],
    "Community Support": ["Community Funding"],
}


# ---------------------------------------------------------------- legacy aliases (migration / normaliser / partner layer)
# Old (pre-v2) term -> new term(s) in the SAME field, or `moved` to another field. Terms that exist unchanged are not listed.
LEGACY_ALIASES = {
    "who_is_it_for": {
        "Need shelter": {"moved": {"what_it_gives": ["Housing/Shelter"]}},
        "Need food support": {"moved": {"what_it_gives": ["Food support"]}},
        "Need mortgage support": {"moved": {"what_it_gives": ["Mortgage assistance"]}},
        "Individuals needing legal aid": {"moved": {"what_it_gives": ["Legal aid and services"]}},
    },
    "what_it_gives": {
        "Referral services": {"to": ["Information and referral services"]},
        "Information services": {"to": ["Information and referral services"]},
        "Rehabilitation services": {"to": ["Rehabilitation services (Physiotherapy/Occupational therapy)"]},  # live-data drift
        "Technology assistance": {"to": ["Technology assistance (internet/computers)"]},  # live-data drift
        "Respite care/Caregiver support": {"to": ["Respite care"], "review": True},  # NCSS 5 Oct; re-tag programmes giving no respite by intervention (R5)
        "Tuition/Enrichment programmes": {"to": ["Tuition", "Enrichment programmes"], "review": True},
        "Home retrofitting and assistive technology": {"to": ["Home retrofitting", "Assistive technology"], "review": True},
        "Child protection services": {"moved": {"scheme_type": ["Protection from Violence"]}},
        "Protection against violence": {"moved": {"scheme_type": ["Protection from Violence"]}},
        "Identification and safety tagging": {"to": []},
        "COVID-19 support": {"to": [], "review": True},
    },
    "scheme_type": {  # removed population terms -> who_is_it_for terms; 14 Oct removals -> what_it_gives / who / re-tag
        "Homelessness Support": {"moved": {"who_is_it_for": ["Homeless"]}},
        "Vocational Training": {"moved": {"what_it_gives": ["Vocational training"]}},
        "Legal Aid": {"moved": {"what_it_gives": ["Legal aid and services"]}},  # 14 Oct sheet supersedes 8 Oct (Justice and legal protection)
        "Residential Care": {"moved": {"what_it_gives": ["Residential care/programmes"]}},
        "Counselling and Emotional Support": {"moved": {"what_it_gives": ["Counselling", "Emotional care"]}, "review": True},
        "Traditional Chinese Medicine (TCM)": {"moved": {"what_it_gives": ["Traditional Chinese Medicine (TCM)"]}},
        "Referral and Information Services": {"moved": {"what_it_gives": ["Information and referral services"]}},
        "Seniors Housing and Home Improvement": {"moved": {"what_it_gives": ["Home retrofitting"]}, "review": True},
        "Elderly Housing and Home Improvement": {"moved": {"what_it_gives": ["Home retrofitting"]}, "review": True},
        "COVID-19 Support": {"to": [], "review": True},
        "Abuse/Family Violence": {"to": [], "review": True},
        "Loss of Breadwinner Support": {"to": [], "review": True},
        "Child and Youth Services": {"to": [], "review": True},  # NCSS 28 Oct split into 3: re-tag per scheme
        "Mental Health Rehabilitation": {"to": ["Mental Health"]},
        "Low Income": {"moved": {"who_is_it_for": ["Low income"]}},
        "Family": {"moved": {"who_is_it_for": ["Families"]}},
        "Children": {"moved": {"who_is_it_for": ["Children"]}},
        "Youth": {"moved": {"who_is_it_for": ["Youth"]}},
        "Youth-at-Risk": {"moved": {"who_is_it_for": ["Youth-at-risk"]}},
        "Women": {"moved": {"who_is_it_for": ["Women"]}},
        "Single Parents": {"moved": {"who_is_it_for": ["Single parents"]}},
        "Elderly": {"moved": {"who_is_it_for": ["Seniors"]}},
        "Persons with Disabilities (PWD)": {"moved": {"who_is_it_for": ["Persons with disabilities (PWDs)"]}},
        "Special Needs": {"moved": {"who_is_it_for": ["Persons with special needs"]}},
        "Foreign Domestic Workers (FDWs)": {"moved": {"who_is_it_for": ["Foreign domestic workers/maids"]}},
        "Migrant Workers/Foreign Workers": {"moved": {"who_is_it_for": ["Migrant workers/Foreign workers"]}},
        "Foreign Spouse/Transnational Family Support": {"moved": {"who_is_it_for": ["Transnational families/Foreign spouses"]}},
        "Incarcerated/Inmate Family Support": {"moved": {"who_is_it_for": ["Families of inmates or ex-offenders"]}},
        "General Public Support": {"moved": {"who_is_it_for": ["General public"]}},
    },
}
