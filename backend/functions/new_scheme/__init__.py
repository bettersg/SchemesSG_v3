"""
New Scheme Processing Module.

This module handles the async processing of new user-submitted schemes:
1. Firestore trigger on schemeEntries collection
2. Lightweight data pipeline (scraping, LLM extraction, town area)
3. Slack notification for human review
4. Approval handling and Firestore updates
"""
