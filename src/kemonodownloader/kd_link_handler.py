"""
Link Handler Module
Extracts and categorizes links from post content
"""

import re
import os
import subprocess
import platform
from urllib.parse import urlparse
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QTextBrowser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QDesktopServices, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QUrl


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


class DownloadedLinksWindow(QDialog):
    """
    Window to display extracted links from posts as clickable links.
    Shows Google Drive, MEGA, and other links found in post content.
    """

    def __init__(self, extracted_links, parent=None):
        """
        Args:
            extracted_links: Dict mapping post_id to links dict
                            {'post_id': {'google_drive': [...], 'mega': [...], 'other': [...]}}
        """
        super().__init__(parent)
        self.extracted_links = extracted_links
        self.setWindowTitle("Extracted Links from Posts")
        self.setModal(False)
        self.resize(900, 700)
        self.setStyleSheet("background: #1A2B4A; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Count total links
        total_links = sum(
            len(links.get('google_drive', [])) +
            len(links.get('mega', [])) +
            len(links.get('other', []))
            for links in self.extracted_links.values()
        )

        # Header label
        header = QLabel(f"Extracted Links from Posts ({total_links} links)")
        header.setStyleSheet("color: white; font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)

        # Text display with clickable links
        self.links_display = QTextBrowser()
        self.links_display.setReadOnly(True)
        self.links_display.setStyleSheet("background: #2A3B5A; border-radius: 5px; padding: 10px; color: white;")
        self.links_display.setOpenExternalLinks(False)  # Handle clicks manually
        self.links_display.anchorClicked.connect(self.open_file_location)
        layout.addWidget(self.links_display)

        # Populate with links
        self.populate_links()

        # Buttons layout
        buttons_layout = QHBoxLayout()

        self.copy_all_btn = QPushButton("Copy All Links")
        self.copy_all_btn.clicked.connect(self.copy_all_paths)
        self.copy_all_btn.setStyleSheet("background: #4A5B7A; padding: 8px; border-radius: 5px; color: white;")
        buttons_layout.addWidget(self.copy_all_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def populate_links(self):
        """Populate the text display with clickable links organized by category."""
        cursor = self.links_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Format for URLs
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#4A9EFF"))
        link_format.setFontUnderline(True)
        link_format.setAnchor(True)

        # Format for headers
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#FFD700"))
        header_format.setFontWeight(QFont.Weight.Bold)

        # Format for post IDs
        post_format = QTextCharFormat()
        post_format.setForeground(QColor("#90EE90"))

        # Normal text format
        normal_format = QTextCharFormat()
        normal_format.setForeground(QColor("white"))

        # Google Drive links
        google_drive_links = [(post_id, links['google_drive'])
                             for post_id, links in self.extracted_links.items()
                             if links.get('google_drive')]
        if google_drive_links:
            cursor.insertText("🔗 GOOGLE DRIVE LINKS\n", header_format)
            cursor.insertText("─" * 80 + "\n\n", normal_format)
            for post_id, urls in google_drive_links:
                cursor.insertText(f"Post ID: {post_id}\n", post_format)
                for url in urls:
                    cursor.insertText("  • ", normal_format)
                    link_format.setAnchorHref(url)
                    cursor.insertText(url, link_format)
                    cursor.insertText("\n", normal_format)
                cursor.insertText("\n", normal_format)

        # MEGA links
        mega_links = [(post_id, links['mega'])
                     for post_id, links in self.extracted_links.items()
                     if links.get('mega')]
        if mega_links:
            cursor.insertText("🔗 MEGA LINKS\n", header_format)
            cursor.insertText("─" * 80 + "\n\n", normal_format)
            for post_id, urls in mega_links:
                cursor.insertText(f"Post ID: {post_id}\n", post_format)
                for url in urls:
                    cursor.insertText("  • ", normal_format)
                    link_format.setAnchorHref(url)
                    cursor.insertText(url, link_format)
                    cursor.insertText("\n", normal_format)
                cursor.insertText("\n", normal_format)

        # Other links
        other_links = [(post_id, links['other'])
                      for post_id, links in self.extracted_links.items()
                      if links.get('other')]
        if other_links:
            cursor.insertText("🔗 OTHER LINKS\n", header_format)
            cursor.insertText("─" * 80 + "\n\n", normal_format)
            for post_id, urls in other_links:
                cursor.insertText(f"Post ID: {post_id}\n", post_format)
                for url in urls:
                    cursor.insertText("  • ", normal_format)
                    link_format.setAnchorHref(url)
                    cursor.insertText(url, link_format)
                    cursor.insertText("\n", normal_format)
                cursor.insertText("\n", normal_format)

        if not google_drive_links and not mega_links and not other_links:
            cursor.insertText("No links found in posts.", normal_format)

        self.links_display.setTextCursor(cursor)

    def open_file_location(self, url):
        """Open the URL in the default browser."""
        url_string = url.toString()
        QDesktopServices.openUrl(QUrl(url_string))

    def open_download_folder(self):
        """Open the links.txt file if it was saved."""
        # This feature is not really needed for URLs, keep button disabled or remove it
        pass

    def copy_all_paths(self):
        """Copy all links to clipboard in organized format."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()

        # Use the same format as the links.txt file
        formatted_content = format_links_file(self.extracted_links)
        clipboard.setText(formatted_content)
