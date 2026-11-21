
from src.data_collection.scraper import (
    extract_page_information
)


def test_extract_page_information():

    html = """
    <html>
        <head>
            <title>AI and ML Programme</title>
            <meta name="description"
                  content="Learn Artificial Intelligence">
        </head>

        <body>
            <h1>AI Programme</h1>
            <h2>Python and Machine Learning</h2>
            <p>Learn AI technologies.</p>
        </body>
    </html>
    """

    result = extract_page_information(
        html,
        "https://example.com/ai-program"
    )

    assert result["page_title"] == "AI and ML Programme"

    assert result["description"] == "Learn Artificial Intelligence"

    assert "AI Programme" in result["headings"]

    assert "Machine Learning" in result["page_text"]
