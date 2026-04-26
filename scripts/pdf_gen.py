import os
from playwright.sync_api import sync_playwright

def generate_pdf():
    html_path = os.path.abspath("docs/substack/musings/prompt_cheat_sheet.html")
    pdf_path = "docs/substack/musings/prompt_cheat_sheet.pdf"

    print(f"Rendering {html_path} to PDF...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{html_path}")
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()

    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"PDF generated: {pdf_path} ({size_kb:.0f} KB)")

if __name__ == "__main__":
    generate_pdf()
