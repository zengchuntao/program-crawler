"""Tests for text utilities."""

from app.util.text_utils import extract_links, html_to_text, looks_like_spa, truncate_text


class TestHtmlToText:
    def test_simple_html(self):
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        text = html_to_text(html)
        assert "Hello" in text
        assert "World" in text

    def test_strips_scripts(self):
        html = "<html><body><script>var x = 1;</script><p>Content</p></body></html>"
        text = html_to_text(html)
        assert "var x" not in text
        assert "Content" in text

    def test_strips_styles(self):
        html = "<html><body><style>.foo { color: red; }</style><p>Visible</p></body></html>"
        text = html_to_text(html)
        assert "color" not in text
        assert "Visible" in text

    def test_empty_html(self):
        assert html_to_text("") == ""

    def test_line_breaks_for_block_elements(self):
        html = "<div>First</div><div>Second</div>"
        text = html_to_text(html)
        assert "First" in text
        assert "Second" in text


class TestTruncateText:
    def test_short_text(self):
        text = "short"
        assert truncate_text(text, 100) == "short"

    def test_long_text(self):
        text = "x" * 200
        result = truncate_text(text, 100)
        assert len(result) > 100  # includes truncation notice
        assert "[... text truncated ...]" in result

    def test_exact_length(self):
        text = "x" * 100
        assert truncate_text(text, 100) == text


class TestLooksLikeSpa:
    def test_regular_html(self):
        body = "<p>Regular page with lots of content.</p>" + "x" * 300
        html = f"<html><body>{body}</body></html>"
        assert looks_like_spa(html) is False

    def test_spa_with_thin_content(self):
        html = '<html><body><div id="root"></div><noscript>Enable JS</noscript></body></html>'
        assert looks_like_spa(html) is True

    def test_spa_with_enough_content(self):
        html = '<html><body><div id="root"><p>' + "Content " * 100 + "</p></div></body></html>"
        assert looks_like_spa(html) is False


class TestExtractLinks:
    def test_absolute_links(self):
        html = (
            '<a href="https://example.com/page1">Link 1</a>'
            '<a href="https://example.com/page2">Link 2</a>'
        )
        links = extract_links(html)
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links

    def test_relative_links_with_base(self):
        html = '<a href="/admissions">Admissions</a>'
        links = extract_links(html, base_url="https://example.com")
        assert "https://example.com/admissions" in links

    def test_deduplication(self):
        html = '<a href="https://example.com">A</a><a href="https://example.com">B</a>'
        links = extract_links(html)
        assert len(links) == 1

    def test_no_links(self):
        html = "<p>No links here</p>"
        links = extract_links(html)
        assert links == []
