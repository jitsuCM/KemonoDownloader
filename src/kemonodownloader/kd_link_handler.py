"""
Link Handler Module
Extracts and categorizes links from post content
"""

import re
from urllib.parse import urlparse


def extract_links(post_content):
    """
    Extract all links from post content, including censored/malformed links.

    Returns a dict categorized by service:
    {
        'google_drive': [...],
        'mega': [...],
        'other': [...]
    }
    """
    if not post_content:
        return {'google_drive': [], 'mega': [], 'other': []}

    links = {
        'google_drive': [],
        'mega': [],
        'other': []
    }

    # Pattern 1: Standard HTTP/HTTPS URLs
    standard_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', post_content, re.IGNORECASE)

    # Pattern 2: URLs without protocol (e.g., "drive.google.com/...")
    no_protocol_urls = re.findall(r'(?:^|[\s>])([a-z0-9-]+\.(?:google\.com|mega\.co\.nz|mega\.nz|mediafire\.com|dropbox\.com|onedrive\.live\.com)[^\s<>"{}|\\^`\[\]]*)', post_content, re.IGNORECASE)

    # Pattern 3: Spaced URLs (e.g., "http:// mega.co.nz / file / ...")
    spaced_urls = re.findall(r'https?\s*:\s*//\s*[a-z0-9-]+(?:\s*\.\s*[a-z0-9-]+)+(?:\s*/\s*[^\s<>"{}|\\^`\[\]]*)?', post_content, re.IGNORECASE)

    # Process standard URLs
    for url in standard_urls:
        categorize_link(url, links)

    # Process no-protocol URLs (add https://)
    for url in no_protocol_urls:
        full_url = f"https://{url}"
        categorize_link(full_url, links)

    # Process spaced URLs (remove spaces)
    for url in spaced_urls:
        cleaned_url = re.sub(r'\s+', '', url)
        categorize_link(cleaned_url, links)

    # Remove duplicates while preserving order
    links['google_drive'] = list(dict.fromkeys(links['google_drive']))
    links['mega'] = list(dict.fromkeys(links['mega']))
    links['other'] = list(dict.fromkeys(links['other']))

    return links


def categorize_link(url, links_dict):
    """Categorize a link into google_drive, mega, or other."""
    url_lower = url.lower()

    if 'drive.google.com' in url_lower or 'docs.google.com' in url_lower:
        links_dict['google_drive'].append(url)
    elif 'mega.co.nz' in url_lower or 'mega.nz' in url_lower:
        links_dict['mega'].append(url)
    else:
        # Only add if it's a valid-looking URL
        if '.' in url and ('/' in url or '?' in url or len(url) > 20):
            links_dict['other'].append(url)


def format_links_file(all_links):
    """
    Format extracted links into a readable text file content.

    Args:
        all_links: Dict mapping post_id to links dict

    Returns:
        Formatted string ready to write to links.txt
    """
    output = []
    output.append("=" * 80)
    output.append("EXTRACTED LINKS FROM POSTS")
    output.append("=" * 80)
    output.append("")

    # Count totals
    total_google_drive = sum(len(links['google_drive']) for links in all_links.values())
    total_mega = sum(len(links['mega']) for links in all_links.values())
    total_other = sum(len(links['other']) for links in all_links.values())

    output.append("SUMMARY:")
    output.append(f"  Google Drive links: {total_google_drive}")
    output.append(f"  MEGA links: {total_mega}")
    output.append(f"  Other links: {total_other}")
    output.append(f"  Total: {total_google_drive + total_mega + total_other}")
    output.append("")
    output.append("=" * 80)
    output.append("")

    # Google Drive section
    if total_google_drive > 0:
        output.append("GOOGLE DRIVE LINKS:")
        output.append("-" * 80)
        for post_id, links in all_links.items():
            if links['google_drive']:
                output.append(f"\nPost ID: {post_id}")
                for link in links['google_drive']:
                    output.append(f"  {link}")
        output.append("")
        output.append("=" * 80)
        output.append("")

    # MEGA section
    if total_mega > 0:
        output.append("MEGA LINKS:")
        output.append("-" * 80)
        for post_id, links in all_links.items():
            if links['mega']:
                output.append(f"\nPost ID: {post_id}")
                for link in links['mega']:
                    output.append(f"  {link}")
        output.append("")
        output.append("=" * 80)
        output.append("")

    # Other links section
    if total_other > 0:
        output.append("OTHER LINKS:")
        output.append("-" * 80)
        for post_id, links in all_links.items():
            if links['other']:
                output.append(f"\nPost ID: {post_id}")
                for link in links['other']:
                    output.append(f"  {link}")
        output.append("")
        output.append("=" * 80)
        output.append("")

    if total_google_drive + total_mega + total_other == 0:
        output.append("No links found in any posts.")
        output.append("")

    return "\n".join(output)
