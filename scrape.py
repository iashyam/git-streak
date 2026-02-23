import urllib.request
import re
from datetime import datetime, timezone

username = "iashyam"
url = f"https://github.com/users/{username}/contributions"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

def calculate_streaks(contributions):
    # Sort contributions by date
    contributions.sort(key=lambda x: x['date'])
    
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    for i, day in enumerate(contributions):
        lvl = day['level']
        
        if lvl > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0
            
    # Check current streak by looking at the last few days
    if not contributions:
        return 0, 0
        
    c_streak = 0
    for day in reversed(contributions):
        if day['level'] > 0:
            c_streak += 1
        else:
            if day == contributions[-1] and c_streak == 0:
                continue
            break
            
    return c_streak, longest_streak

def update_html(total, c_streak, l_streak, contributions):
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()
    
    heatmap_html = ""
    for day in contributions:
        heatmap_html += f'<div class="heatmap-day" data-level="{day["level"]}" data-tooltip="{day["elementText"]}"></div>\n                        '
        
    updated_at = f"Last updated: {datetime.now(timezone.utc).strftime('%b %d, %Y, %H:%M UTC')}"

    # Replace values using the comment tags
    content = re.sub(
        r'<!--TEMPLATE:CURRENT_STREAK-->.*?<!--ENDTEMPLATE-->',
        f'<!--TEMPLATE:CURRENT_STREAK-->{c_streak} day{"s" if c_streak != 1 else ""}<!--ENDTEMPLATE-->',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'<!--TEMPLATE:LONGEST_STREAK-->.*?<!--ENDTEMPLATE-->',
        f'<!--TEMPLATE:LONGEST_STREAK-->{l_streak} day{"s" if l_streak != 1 else ""}<!--ENDTEMPLATE-->',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'<!--TEMPLATE:TOTAL-->.*?<!--ENDTEMPLATE-->',
        f'<!--TEMPLATE:TOTAL-->{total:,}<!--ENDTEMPLATE-->',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'<!--TEMPLATE:UPDATED-->.*?<!--ENDTEMPLATE-->',
        f'<!--TEMPLATE:UPDATED-->{updated_at}<!--ENDTEMPLATE-->',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'<!--TEMPLATE:HEATMAP-->.*?<!--ENDTEMPLATE-->',
        f'<!--TEMPLATE:HEATMAP-->\n                        {heatmap_html.strip()}\n                        <!--ENDTEMPLATE-->',
        content,
        flags=re.DOTALL
    )

    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(content)

try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        
        # Regex to find <td ... data-date="YYYY-MM-DD" ... data-level="L">
        days = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})".*?data-level="(\d+)"', html)
        if not days:
            days = re.findall(r'data-level="(\d+)".*?data-date="(\d{4}-\d{2}-\d{2})"', html)
            days = [(d[1], int(d[0])) for d in days]
        else:
            days = [(d[0], int(d[1])) for d in days]
            
        contributions = []
        for date_str, level in days:
            contributions.append({
                "date": date_str,
                "level": level,
                "elementText": f"Level {level} on {date_str}" if level > 0 else f"No contributions on {date_str}"
            })

        current_streak, longest_streak = calculate_streaks(contributions)
        
        total_match = re.search(r'>\s*([\d,]+)\s+contributions', html, re.IGNORECASE)
        total_count = int(total_match.group(1).replace(',', '')) if total_match else 0

        # Update the HTML file directly instead of data.json
        update_html(total_count, current_streak, longest_streak, contributions)
            
        print(f"Scrape successful! HTML Updated. Current Streak: {current_streak}. Longest Streak: {longest_streak}.")
        
except Exception as e:
    print("Error:", e)
    raise e
