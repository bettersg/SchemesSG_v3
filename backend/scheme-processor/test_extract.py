 # test_extract.py
import asyncio
from app.services.scraper import scrape_url
from app.services.llm_extractor import extract_with_llm
from app.services.extraction import extract_contacts
import json

async def main():
    url = "https://www.salvationarmy.org.sg/wwd-gracehaven/"  # replace with your test
    url = "https://childrensaidsociety.org.sg/melrose-home/"  # replace with your test


    print(f"Scraping {url}...")
    scrape_result = await scrape_url(url)
    content = scrape_result.get("content", "")
    print(f"Scraped {len(content)} chars")

    print("\n--- LLM Extraction ---")
    llm_fields = await extract_with_llm(content)
    print(json.dumps(llm_fields, indent=2, default=str))

    print("\n--- Regex Contacts ---")
    contacts = extract_contacts(content)
    print(f"Emails: {contacts.emails}")
    print(f"Phones: {contacts.phones}")

asyncio.run(main())
