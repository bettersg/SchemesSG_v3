"""NCSS-aligned taxonomy for Schemes SG (Phase 1 draft, local only).

Source: NCSS Programme Taxonomy v1.0 (20 Jul 2026) + "Mapping of NCSS & Schemes SG Taxos.xlsx".
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
    "Migrant individuals": "Persons not native to Singapore who may face language, cultural or legal barriers to settling here, e.g. for employment or studies.",
    "Families": "Families in general, incl. preventive, parenting, marriage and family programmes not limited to multi-stressed families. (NCSS asked to add as broad profile.)",
    # NCSS suggested adding these three; parent unconfirmed.
    "Homeless": "Persons without access to stable and safe accommodation, who may sleep in public spaces or move between temporary housing. (NCSS definition, xlsx Sheet3.)",
    "Inmates / persons in custody": "Persons currently in custody or incarcerated.",
    "Victims of abuse or harassment": "Persons who have experienced abuse, family violence or harassment.",
}

NEEDS = [
    "Caregiving", "Community participation/Engagement", "Counselling & Crisis Support", "Education and Learning",
    "Work & Employment", "Financial & Material Support", "Fostering & Alternative Care", "Healthcare & Well-Being",
    "Home maintenance", "Housing & Shelter Support", "Intrapersonal Challenges", "Retirement & Legacy Planning",
    "Legal Services", "Family, Parenting & Relationships", "Mental Health Services", "Disability Support",
    "Personal Development", "Recreational Activities", "Reintegration/Transition Services", "Social support",
    "Substance and Behavioral Addictions recovery",
]

INTERVENTIONS = [
    "Befriending", "Care Services", "Casework/Case Management", "Coaching", "Community Development/Outreach",
    "Counselling", "Crisis Assessment & Intervention", "Enrichment Activities", "Financial/Material Assistance",
    "Group Work", "Helpline/Hotline", "Housing & Shelter Support", "Home Maintenance", "Information & Referral",
    "Information & Communication Accessibility", "Learning Intervention", "Legal Services",
    "Medical Clinic & Services", "Mentoring", "Mobility Services", "Psychoeducation", "Therapy", "Training",
    "Transportation", "Tuition", "Job Placement",
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
# behavioural addictions. "Elderly" kept (rename to Seniors is a partner-breaking change; open item).
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
    T("Elderly", "Persons aged 60 and above (NCSS: Seniors).", age=["Seniors"]),
    T("Elderly with dementia", "Persons aged 60+ diagnosed with dementia, and their care.", age=["Seniors"], profile=["Chronically ill"]),
    T("Persons with disabilities (PWDs)", "Persons with permanent intellectual or physical disabilities (e.g. mobility, vision, hearing, intellectual disability, cerebral palsy). Mental health conditions are NOT disabilities.", profile=["Persons with disabilities"]),
    T("Persons with special needs", "Persons with developmental or learning needs (e.g. SPED students). Treat as disability only when the disability is permanent.", profile=["Persons with disabilities"]),
    T("Persons on autism spectrum", "Persons diagnosed with autism spectrum disorder.", profile=["Persons with disabilities"]),
    T("Persons with chronic or terminal illnesses", "Persons with long-term, persistent or terminal illness requiring ongoing management (e.g. cancer, kidney failure, diabetes).", profile=["Chronically ill"]),
    T("Persons with mental health issues", "Persons diagnosed with, or severely affected by, mental health conditions (e.g. depression, schizophrenia). Recoverable, so NOT persons with disabilities.", profile=["Persons with mental health conditions"]),
    T("Persons with substance and behavioural addictions", "Persons dependent on substances or compulsive behaviours (drugs, alcohol, gambling, gaming).", profile=["Persons with substance and behavioural addictions"]),
    T("Individuals with gambling addiction", "Persons with a gambling addiction or problem gambling, and affected family.", profile=["Persons with substance and behavioural addictions"]),
    T("Caregivers", "People providing ongoing primary care to someone with care needs from age, disability, illness or mental health condition.", profile=["Caregiver"], note="check vs NCSS Caregiver def"),
    T("Low income", "Individuals/households with insufficient income, incl. those on means-tested schemes.", profile=["Persons with financial difficulties"]),
    T("Low income families", "Families with low household income.", profile=["Persons with financial difficulties", "Families"]),
    T("Low income elderly", "Persons aged 60+ with low income.", age=["Seniors"], profile=["Persons with financial difficulties"]),
    T("Facing financial hardship", "Persons or households in temporary or acute financial difficulty (job loss, debt, emergencies).", profile=["Persons with financial difficulties"]),
    T("Unemployed", "Persons not in paid work, available for and seeking work.", profile=["Unemployed"]),
    T("Retrenched", "Persons who lost their job through retrenchment.", profile=["Unemployed"]),
    T("Homeless", "Persons without stable, safe accommodation, sleeping rough or moving between temporary housing.", profile=["Homeless"], provisional=True, fallback=["Persons with financial difficulties"]),
    T("Foreign domestic workers/maids", "Foreign domestic workers (maids) employed in Singapore households, and their employers when the scheme is for FDW matters.", profile=["Migrant individuals"]),
    T("Migrant workers/Foreign workers", "Foreign workers in Singapore on work passes (e.g. construction, marine).", profile=["Migrant individuals"]),
    T("Transnational families/Foreign spouses", "Foreign spouses of Singaporeans and cross-border families.", profile=["Migrant individuals", "Families"]),
    T("Ex-offenders", "Persons who completed a sentence and are reintegrating.", profile=["Ex-offender"]),
    T("Inmates", "Persons currently in prison or custody.", profile=["Inmates / persons in custody"], provisional=True, fallback=["Ex-offender"]),
    T("Families of inmates or ex-offenders", "Family members of inmates or ex-offenders.", profile=["Families"]),
    T("Victims of abuse or harassment", "Persons experiencing or who experienced abuse, family violence, or harassment.", profile=["Victims of abuse or harassment"], provisional=True, fallback=["Multi-stressed family"]),
    T("Facing end of life", "Persons with a life-limiting illness nearing end of life, and their families.", profile=["Chronically ill"], note="NCSS: circumstance; review under needs"),
    T("Individuals struggling with loss", "Persons bereaved or grieving. Circumstance, not a population.", note="NCSS: circumstance"),
    T("Malay/Muslim community", "Programme targeted at Malay/Muslim community. Demographic marker.", note="NCSS: metadata"),
    T("Indian community", "Programme targeted at Indian community. Demographic marker.", note="NCSS: metadata"),
    T("Chinese community", "Programme targeted at Chinese community. Demographic marker.", note="NCSS: metadata"),
    T("General public", "Open to all residents with no specific target group. Use ONLY if no other term fits.", note="NCSS: access descriptor"),
]
# NB: Gap check vs constants.py (43): -4 moved need terms +3 added = 42 here? count asserted in tests.

# ---------------------------------------------------------------- what_it_gives
def G(name, definition, *interventions):
    return Term(name, definition, (), tuple(interventions))  # 'profile' slot reused = intervention parents


WHAT_IT_GIVES = [
    G("Counselling", "Professional guidance by trained counsellors for personal or family issues.", "Counselling"),
    G("Casework", "Coordinated assessment, planning and monitoring of a person's needs by a social worker.", "Casework/Case Management"),
    G("Emotional care", "Emotional support and companionship, non-clinical.", "Befriending", "Counselling"),
    G("Mental health assessment and treatment", "Clinical assessment/treatment of mental health conditions by clinicians.", "Therapy", "Medical Clinic & Services"),
    G("Psychological support/Psychotherapy", "Structured psychological therapy by qualified therapists.", "Therapy"),
    G("Befriending services", "Regular companionship to reduce isolation.", "Befriending"),
    G("Helpline services", "Phone/digital helpline support.", "Helpline/Hotline"),
    G("Referral services", "Connecting people to appropriate services.", "Information & Referral"),
    G("Educational programmes", "Structured learning or awareness programmes.", "Psychoeducation", "Training"),
    G("Vocational training", "Skills training for employment.", "Training"),
    G("Employment assistance", "Help to find, keep or advance in a job.", "Job Placement", "Coaching"),
    G("Skills training and job matching", "Skills upgrading with job placement.", "Training", "Job Placement"),
    G("Financial assistance (general)", "Cash or material help for general needs.", "Financial/Material Assistance"),
    G("Financial assistance for daily living expenses", "Help with everyday living costs.", "Financial/Material Assistance"),
    G("Financial assistance for healthcare", "Help paying medical bills or care.", "Financial/Material Assistance"),
    G("Financial assistance for chronic or terminal illnesses", "Funding for long-term/terminal illness care.", "Financial/Material Assistance"),
    G("Financial assistance for education", "Bursaries, fee or school-cost help.", "Financial/Material Assistance"),
    G("Financial assistance for kindergarten/student care", "Subsidies for preschool/student care.", "Financial/Material Assistance"),
    G("Financial assistance for assistive technology and medical equipment", "Funding for assistive devices/equipment.", "Financial/Material Assistance"),
    G("Financial assistance for housing", "Help with rent, housing costs.", "Financial/Material Assistance", "Housing & Shelter Support"),
    G("Mortgage assistance", "Help paying home loans.", "Financial/Material Assistance"),
    G("Debt assistance", "Help managing or repaying debt.", "Financial/Material Assistance", "Casework/Case Management"),
    G("Burial and emergency assistance", "Funeral or emergency cash aid.", "Financial/Material Assistance"),
    G("Food support", "Food distribution, vouchers, meals.", "Financial/Material Assistance"),
    G("Housing/Shelter", "Temporary or transitional shelter or housing help.", "Housing & Shelter Support"),
    G("Respite care/Caregiver support", "Temporary relief and support for caregivers.", "Care Services"),
    G("Elder sitting and caregiving services", "Home or centre sitting/caregiving for seniors.", "Care Services"),
    G("Child protection services", "Protection and intervention for children at risk.", "Crisis Assessment & Intervention", "Casework/Case Management"),
    G("Childcare services", "Care for children while parents are away.", "Care Services"),
    G("Babysitting/Childcare services", "Babysitting and childcare.", "Care Services"),
    G("Student care", "After-school care.", "Care Services"),
    G("Tuition/Enrichment programmes", "Academic tuition or enrichment.", "Tuition", "Enrichment Activities"),
    G("Transport subsidies", "Subsidised fares/transport.", "Transportation", "Financial/Material Assistance"),
    G("Medical transport assistance", "Transport to medical appointments.", "Transportation"),
    G("Healthcare (general/basic services)", "General clinic and basic health services.", "Medical Clinic & Services"),
    G("Dental services", "Dental care.", "Medical Clinic & Services"),
    G("Traditional Chinese Medicine (TCM)", "TCM clinics and services.", "Medical Clinic & Services"),
    G("Rehabilitation services (Physiotherapy/Occupational therapy)", "Physio/occupational rehabilitation.", "Therapy"),
    G("Legal aid and services", "Legal advice, aid and representation.", "Legal Services"),
    G("Protection against violence", "Safety, protection orders, shelters for violence.", "Crisis Assessment & Intervention"),
    G("Residential care/programmes", "Live-in care or programmes.", "Care Services"),
    G("Addictions treatment and rehabilitation", "Treatment and recovery support for addictions.", "Therapy", "Group Work"),
    G("Social and recreational activities", "Group social, recreational, exercise and active-ageing activities for engagement and connection.", "Enrichment Activities", "Group Work"),
    G("Support groups", "Facilitated peer or group support.", "Group Work"),
    G("Bereavement support", "Support for grief and loss.", "Counselling", "Group Work"),
    G("End-of-life care", "Palliative and end-of-life care.", "Care Services", "Medical Clinic & Services"),
    G("Identification and safety tagging", "ID/safety tags e.g. for persons prone to wandering.", "Care Services"),
    G("Subsidies for Foreign Domestic Workers (FDWs)", "Subsidies for hiring/training FDWs.", "Financial/Material Assistance"),
    G("Retirement and financial planning assistance", "Advice on retirement/financial planning.", "Information & Referral", "Coaching"),
    G("Benefits and perks for PWDs (transport, discounts, facilities)", "Concessions for persons with disabilities.", "Financial/Material Assistance", "Mobility Services"),
    G("Technology assistance (internet/computers)", "Devices, internet access, digital help.", "Financial/Material Assistance", "Training"),
    G("Home retrofitting and assistive technology", "Home modifications/assistive devices.", "Home Maintenance", "Mobility Services"),
    G("Funding for community projects", "Grants for community initiatives.", "Community Development/Outreach"),
    G("COVID-19 support", "COVID-19 relief (legacy).", "Financial/Material Assistance"),
    G("Information services", "Information and guidance.", "Information & Referral"),
]

# ---------------------------------------------------------------- scheme_type (need domains only)
# Population terms removed (15). Parent = NCSS Service User Need(s).
def N(name, definition, *needs):
    return Term(name, definition, (), tuple(needs))


SCHEME_TYPE = [
    N("Family and Parenting Support", "Parenting, marriage, family relationship and family life support.", "Family, Parenting & Relationships"),
    N("Disability Support", "Support for persons with disabilities: mobility, daily living, centre/home-based care, accessibility.", "Disability Support"),
    N("Active Ageing and Social Activities", "Social, recreational and active-ageing activities that keep seniors (or others) engaged and connected.", "Recreational Activities", "Social support"),
    N("Caregiver Support", "Training, respite and support for caregivers.", "Caregiving"),
    N("Ex-offender Support", "Reintegration support for ex-offenders.", "Reintegration/Transition Services"),
    N("Education Support", "Tuition, learning support, school-related help.", "Education and Learning"),
    N("Student Care Support", "After-school and student care.", "Education and Learning", "Family, Parenting & Relationships"),
    N("Healthcare", "Treatment and prevention of physical health issues.", "Healthcare & Well-Being"),
    N("Dental Healthcare", "Dental care.", "Healthcare & Well-Being"),
    N("Traditional Chinese Medicine (TCM)", "TCM services.", "Healthcare & Well-Being"),
    N("General Healthcare Subsidies", "Subsidies for medical costs.", "Healthcare & Well-Being", "Financial & Material Support"),
    N("Chronic or Terminal Illness Support", "Support for long-term/terminal illness.", "Healthcare & Well-Being"),
    N("Mental Health", "Emotional support and treatment for mental health.", "Mental Health Services"),
    N("Mental Health Rehabilitation", "Recovery and rehabilitation for mental health.", "Mental Health Services", "Reintegration/Transition Services"),
    N("Counselling and Emotional Support", "Counselling and emotional support.", "Counselling & Crisis Support", "Mental Health Services"),
    N("End-of-Life/Palliative Care", "Palliative and end-of-life care.", "Healthcare & Well-Being", "Retirement & Legacy Planning"),
    N("Food Support", "Food and meals.", "Financial & Material Support"),
    N("Housing/Shelter", "Shelter and housing.", "Housing & Shelter Support"),
    N("Homelessness Support", "Support for homeless persons.", "Housing & Shelter Support"),
    N("Elderly Housing and Home Improvement", "Home upgrades/repairs for seniors.", "Home maintenance", "Housing & Shelter Support"),
    N("Employment Support", "Help finding and keeping work.", "Work & Employment"),
    N("Vocational Training", "Job skills training.", "Work & Employment", "Education and Learning"),
    N("Financial Assistance", "Cash or material aid.", "Financial & Material Support"),
    N("Debt Assistance", "Debt management.", "Financial & Material Support"),
    N("Loss of Breadwinner Support", "Support after loss of family income earner.", "Financial & Material Support"),
    N("Financial Planning and Retirement Support", "Retirement and financial planning.", "Retirement & Legacy Planning"),
    N("Transport Support", "Transport help.", "Disability Support", "Financial & Material Support"),
    N("Technology Support", "Digital access and assistive tech.", "Disability Support", "Education and Learning"),
    N("Legal Aid", "Legal advice and aid.", "Legal Services"),
    N("Abuse/Family Violence", "Family violence and abuse response.", "Counselling & Crisis Support"),
    N("Protection from Violence", "Protection against violence.", "Counselling & Crisis Support"),
    N("COVID-19 Support", "COVID-19 relief (legacy).", "Financial & Material Support"),
    N("Community Funding", "Funding for community projects.", "Community participation/Engagement"),
    N("Residential Care", "Live-in care.", "Disability Support", "Caregiving"),
    N("Addictions Rehabilitation", "Addiction recovery.", "Substance and Behavioral Addictions recovery"),
    N("Referral and Information Services", "Information and referrals.", "Social support"),
]

REMOVED_FROM_SCHEME_TYPE = [
    "Low Income", "Family", "Children", "Youth", "Youth-at-Risk", "Women", "Single Parents", "Elderly",
    "Persons with Disabilities (PWD)", "Special Needs", "Foreign Domestic Workers (FDWs)",
    "Migrant Workers/Foreign Workers", "Foreign Spouse/Transnational Family Support",
    "Incarcerated/Inmate Family Support", "General Public Support",
]
MOVED_OUT_OF_WHO = {  # who term -> what_it_gives term
    "Need shelter": "Housing/Shelter", "Need food support": "Food support",
    "Need mortgage support": "Mortgage assistance", "Individuals needing legal aid": "Legal aid and services",
}


# ---------------------------------------------------------------- age bands (applied in CODE from age_min/age_max)
# Rule (user, 2026-09-29): tag EVERY band the stated range overlaps. Open-ended max = no upper bound.
AGE_BAND_TERMS = [  # (term, lo, hi)
    ("Infants and toddlers (0-3)", 0, 3), ("Preschool children (4-6)", 4, 6),
    ("Primary school children (7-12)", 7, 12), ("Children", 0, 12),
    ("Teenagers (13-17)", 13, 17), ("Youth", 13, 21),
    ("Adults", 22, 59), ("Elderly", 60, 200),
]
AGE_TERM_NAMES = {t for t, _, _ in AGE_BAND_TERMS}


def age_terms(age_min, age_max):
    """Terms whose band overlaps [age_min, age_max]; None bounds are open. Returns None if no age given."""
    if age_min is None and age_max is None:
        return None
    lo = 0 if age_min is None else age_min
    hi = 200 if age_max is None else age_max
    return {t for t, a, b in AGE_BAND_TERMS if lo <= b and hi >= a}
