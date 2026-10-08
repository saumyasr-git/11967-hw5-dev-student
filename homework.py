import argparse
import re
import string

import requests
from bs4 import BeautifulSoup, UnicodeDammit

from utils import read_warc_file

# you might need to import other modules depending on your implementation

def retrieve_bad_words() -> set[str]:
    """Helper function - that reads a list of bad words from a file and returns them as a set.
    Returns:
        Set[str]: A set containing lowercase bad words.
    """
    with open('./bad_word_list.txt', 'r') as file:
        records = file.read().strip().split('\n')
        bad_words = [record.lower() for record in records]
        return set(bad_words)

from bs4 import BeautifulSoup, UnicodeDammit

def html_to_text(html):
    # Use UnicodeDammit to auto‑detect encoding
    if isinstance(html, bytes):
        html = html.decode("shift_jis", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

from bs4 import UnicodeDammit
import re



def replace_pii(text: str) -> str:
    """Masks personally identifiable information (PII) from text with the specified masking formats.
    Args: 
        text (str): Candidate text.
    Returns:
        str: Text with PII obfuscated.
    """
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "XXX-XX-XXXX", text)
    text = re.sub(r"\+1\s*\d{10}", "+1 XXXXXXXXXX", text)
   
    return text

def clean_text(text: str) -> str:
    """Removes substrings identified as low-quality according to alphanumeric, whitespace and valid document checks.  
    Args:
        text (str): document to process.
    Returns:
        str: cleaned document
    """
    paragraphs = text.split("\n")
    filtered = []

    for p in paragraphs:
        has_long_run = bool(re.search(r"\S{101,}", p))
        has_punctuation = any(ch in string.punctuation for ch in p)

        if has_long_run or not has_punctuation:
            continue

        filtered.append(p)

    return "\n".join(filtered)
def heuristic_quality_filter(text: str) -> bool:
    """Rejects documents based on the rules.
    Args:
        text (str): document to check
    Returns:
        bool: returns True if the document passes the four filters, False otherwise.
    """
    allowed = set(string.ascii_letters + string.digits + string.punctuation + string.whitespace)


    valid = sum(1 for ch in text if ch in allowed)
    for word in text.split():
        normalized = word.lower().strip(string.punctuation)
        if normalized in retrieve_bad_words():
            return False

    if not any(ch in string.punctuation for ch in text):
        return False
    if not text or not text.strip():
        return False
    if not (valid / len(text)) >= 0.80:
        return False
    return True

   
        
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname', type=str, default='data.warc', help='Specify the path for your warc file.')
    parser.add_argument('--num_records', type=int, default=6368
                        , help='Specify the number of records you want to parse (only used for debugging with smaller sets)')
    args = parser.parse_args()
  
    
    if args.fname:
        kept_count = 0
        html_count =0
      
        for _, _ in read_warc_file(args.fname):
            html_count += 1
        print(f"Total html in shard: {html_count}")

        for url, html_text in read_warc_file(args.fname, args.num_records):
            
            text = html_to_text(html_text)

            raw_suspicious = (
                re.search(r"\S{101,}", text) or
                not any(ch in string.punctuation for ch in text)
            )

            cleaned_text = clean_text(text)
            cleaned_nopii_text = replace_pii(cleaned_text)
            passes_check = heuristic_quality_filter(cleaned_nopii_text)

            if passes_check:
                kept_count += 1

            '''if raw_suspicious and passes_check:
                print(f"Escaped low-quality page: {url}")
                try:
                    response = requests.get(url, timeout=20)
                    print("HTTP status:", response.status_code)
                    print(response.text[:2000])
                except Exception as e:
                    print(f"Could not fetch {url}: {e}")'''

        print(f"Documents left after cleanup: {kept_count}")
        
    else:
        print("Usage: python homework.py --fname data.warc")