# Partner notice — draft (send from Eugene)

**Subject:** Schemes.sg tag vocabulary is changing to the NCSS taxonomy — please review on dev by <DATE + 7 days>

Hi <partner>,

Schemes.sg is aligning its scheme tags with the NCSS Programme Taxonomy v1.0. The three tag fields on every scheme, `who_is_it_for`, `what_it_gives` and `scheme_type`, will change values, and every scheme is being re-tagged. Field names and the API shape do not change. Values you filter or map on may.

**What changes**
- Some terms are renamed (e.g. Elderly → Seniors).
- 12 `scheme_type` values are removed. Their meaning moves to `who_is_it_for` or `what_it_gives`, or schemes are re-tagged individually.
- Tags are re-assigned by a model against NCSS definitions, so individual schemes can gain or lose tags beyond the renames below.
- Mental health conditions are no longer counted as disabilities.

**Review on dev (1 week)**
Dev API: <URL + key instructions>. Dev site: <stg URL>. Please check the parts of your integration that read these three fields, and reply with anything that breaks or any mapping you'd want different. Production changes only after NCSS and partner review.

**Old → new term mapping** (terms not listed are unchanged)

| Field | Old term | New |
|---|---|---|
| scheme_type | Abuse/Family Violence | Removed; each scheme re-tagged by what it delivers |
| scheme_type | COVID-19 Support | Removed; each scheme re-tagged by what it delivers |
| scheme_type | Children | Moved to who_is_it_for: Children |
| scheme_type | Counselling and Emotional Support | Moved to what_it_gives: Counselling, Emotional care (re-tagged per scheme) |
| scheme_type | Elderly | Moved to who_is_it_for: Seniors |
| scheme_type | Elderly Housing and Home Improvement | Moved to what_it_gives: Home retrofitting (re-tagged per scheme) |
| scheme_type | Family | Moved to who_is_it_for: Families |
| scheme_type | Foreign Domestic Workers (FDWs) | Moved to who_is_it_for: Foreign domestic workers/maids |
| scheme_type | Foreign Spouse/Transnational Family Support | Moved to who_is_it_for: Transnational families/Foreign spouses |
| scheme_type | General Public Support | Moved to who_is_it_for: General public |
| scheme_type | Homelessness Support | Moved to who_is_it_for: Homeless |
| scheme_type | Incarcerated/Inmate Family Support | Moved to who_is_it_for: Families of inmates or ex-offenders |
| scheme_type | Legal Aid | Moved to what_it_gives: Legal aid and services |
| scheme_type | Loss of Breadwinner Support | Removed; each scheme re-tagged by what it delivers |
| scheme_type | Low Income | Moved to who_is_it_for: Low income |
| scheme_type | Mental Health Rehabilitation | Now Mental Health |
| scheme_type | Migrant Workers/Foreign Workers | Moved to who_is_it_for: Migrant workers/Foreign workers |
| scheme_type | Persons with Disabilities (PWD) | Moved to who_is_it_for: Persons with disabilities (PWDs) |
| scheme_type | Referral and Information Services | Moved to what_it_gives: Information and referral services |
| scheme_type | Residential Care | Moved to what_it_gives: Residential care/programmes |
| scheme_type | Seniors Housing and Home Improvement | Moved to what_it_gives: Home retrofitting (re-tagged per scheme) |
| scheme_type | Single Parents | Moved to who_is_it_for: Single parents |
| scheme_type | Special Needs | Moved to who_is_it_for: Persons with special needs |
| scheme_type | Traditional Chinese Medicine (TCM) | Moved to what_it_gives: Traditional Chinese Medicine (TCM) |
| scheme_type | Vocational Training | Moved to what_it_gives: Vocational training |
| scheme_type | Women | Moved to who_is_it_for: Women |
| scheme_type | Youth | Moved to who_is_it_for: Youth |
| scheme_type | Youth-at-Risk | Moved to who_is_it_for: Youth-at-risk |
| what_it_gives | COVID-19 support | Removed; each scheme re-tagged by what it delivers |
| what_it_gives | Child protection services | Moved to scheme_type: Child and Youth Services |
| what_it_gives | Elder sitting and caregiving services | Renamed to Senior sitting and caregiving services |
| what_it_gives | Home retrofitting and assistive technology | Now Home retrofitting, Assistive technology (re-tagged per scheme) |
| what_it_gives | Identification and safety tagging | Removed; each scheme re-tagged by what it delivers |
| what_it_gives | Information services | Now Information and referral services |
| what_it_gives | Protection against violence | Moved to scheme_type: Protection from Violence |
| what_it_gives | Referral services | Now Information and referral services |
| what_it_gives | Rehabilitation services | Now Rehabilitation services (Physiotherapy/Occupational therapy) |
| what_it_gives | Respite care/Caregiver support | Now Respite care (re-tagged per scheme) |
| what_it_gives | Technology assistance | Now Technology assistance (internet/computers) |
| what_it_gives | Tuition/Enrichment programmes | Now Tuition, Enrichment programmes (re-tagged per scheme) |
| who_is_it_for | Elderly | Renamed to Seniors |
| who_is_it_for | Elderly with dementia | Renamed to Seniors with dementia |
| who_is_it_for | Individuals needing legal aid | Moved to what_it_gives: Legal aid and services |
| who_is_it_for | Low income elderly | Renamed to Low income seniors |
| who_is_it_for | Need food support | Moved to what_it_gives: Food support |
| who_is_it_for | Need mortgage support | Moved to what_it_gives: Mortgage assistance |
| who_is_it_for | Need shelter | Moved to what_it_gives: Housing/Shelter |
| who_is_it_for | Persons with mental health issues | Renamed to Persons with mental health conditions |

Questions: <contact>.
