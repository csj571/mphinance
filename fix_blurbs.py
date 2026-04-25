import re
import yfinance as yf

file_path = 'docs/substack/musings/2026-04-18_35-stock-portfolio.md'
with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    match = re.match(r'^(\d+\.\s+\*\*([A-Z-]+)\*\*\s+-\s+\[Deep Dive\]\([^)]+\)\s+:\s+\*)(.*)(\*\s*)$', line)
    if match:
        base_str = match.group(1)
        ticker = match.group(2)
        blurb = match.group(3)
        end_str = match.group(4)
        
        if blurb == "A leading company in its respective sector." or len(blurb.split()) < 5:
            # Try to fetch from yfinance
            try:
                info = yf.Ticker(ticker).info
                summary = info.get('longBusinessSummary', '')
                if summary:
                    blurb = summary.split('. ')[0].strip()
                    if not blurb.endswith('.'):
                        blurb += '.'
            except Exception as e:
                pass
                
        new_line = f"{base_str}{blurb}{end_str}\n"
        new_lines.append(new_line)
    else:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("Fixed missing blurbs.")
