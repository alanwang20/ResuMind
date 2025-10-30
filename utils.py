import re
from collections import Counter
from typing import Dict, List, Tuple

COMMON_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
    'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
    'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'just', 'about', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'up', 'down', 'out', 'off',
    'over', 'any', 'our', 'their', 'your', 'its'
}


def clean_text(text: str) -> str:
    """Clean and normalize text for processing."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_ngrams(text: str, n: int = 1) -> List[str]:
    """Extract n-grams from text."""
    words = clean_text(text).split()
    words = [w for w in words if w not in COMMON_STOPWORDS and len(w) > 2]
    
    if n == 1:
        return words
    
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)
    return ngrams


def top_ngrams(text: str, top_k: int = 20) -> List[Tuple[str, int]]:
    """Extract top n-grams (1-grams and 2-grams combined)."""
    unigrams = extract_ngrams(text, n=1)
    bigrams = extract_ngrams(text, n=2)
    
    all_grams = unigrams + bigrams
    counter = Counter(all_grams)
    
    return counter.most_common(top_k)


def simple_ats_report(job_text: str, user_text: str, top_k: int = 20) -> Dict:
    """
    Generate a simple ATS keyword match report.
    
    Returns:
        dict with 'top_matches' (list of tuples) and 'top_gaps' (list of strings)
    """
    job_keywords = top_ngrams(job_text, top_k=top_k * 2)
    
    user_text_clean = clean_text(user_text)
    
    matches = []
    gaps = []
    
    for keyword, job_count in job_keywords:
        count_in_user = user_text_clean.count(keyword)
        
        if count_in_user > 0:
            matches.append((keyword, count_in_user))
        else:
            gaps.append(keyword)
    
    matches = sorted(matches, key=lambda x: x[1], reverse=True)[:top_k]
    gaps = gaps[:10]
    
    return {
        'top_matches': matches,
        'top_gaps': gaps
    }


def safe_markdown_download(content: str, filename: str) -> Tuple[str, str]:
    """
    Prepare content for markdown download.
    
    Returns:
        tuple of (content, mimetype)
    """
    if not filename.endswith('.md'):
        filename += '.md'
    
    return content, 'text/markdown'


def truncate_log(text: str, max_length: int = 200) -> str:
    """Truncate text for logging purposes."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [{len(text)} chars total]"
