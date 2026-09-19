"""Generate a self-contained animated SVG from GitHub contribution data.

Python standard library only. --demo is explicitly labelled sample data.
Production failures never silently replace real data with samples.
"""
import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request


def fetch_calendar(username):
    token = os.environ.get('GH_TOKEN')
    if not token:
        raise RuntimeError('GH_TOKEN ausente. Execute pelo GitHub Actions.')
    query = '''query($login:String!) {
      user(login:$login) { contributionsCollection {
        contributionCalendar { totalContributions weeks {
          contributionDays { date weekday contributionCount contributionLevel }
        } }
      } }
    }'''
    request = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'login': username}}).encode(),
        headers={'Authorization': 'Bearer ' + token,
                 'Content-Type': 'application/json', 'User-Agent': 'profile-wolf'})
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.load(response)
    if result.get('errors') or not result.get('data', {}).get('user'):
        raise RuntimeError('GitHub não retornou o calendário: ' +
                           json.dumps(result.get('errors', [])))
    return result['data']['user']['contributionsCollection']['contributionCalendar']


def demo_calendar():
    start = dt.date(2025, 9, 21)
    weeks = []
    levels = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE',
              'THIRD_QUARTILE', 'FOURTH_QUARTILE']
    for w in range(53):
        days = []
        for row in range(7):
            n = (w * 13 + row * 7) % 11
            level = n % 5 if n < 7 else 0
            days.append({'date': str(start + dt.timedelta(days=w * 7 + row)),
                         'weekday': row, 'contributionCount': level * 2,
                         'contributionLevel': levels[level]})
        weeks.append({'contributionDays': days})
    return {'weeks': weeks, 'totalContributions': sum(
        d['contributionCount'] for w in weeks for d in w['contributionDays'])}


def wolf():
    # Editable vector pixel-art character. Facing right, with articulated legs.
    return '''<g shape-rendering="crispEdges" transform="translate(-23 -32)">
      <g fill="#1d4ed8" stroke="#071d3c" stroke-width="1">
        <path d="M14 20H7V16H3V10H0V23H5V28H14Z"/>
        <path d="M12 18H26V14H31V7H34V0H37V8H41V3H44V15H48V19H54V24H48V29H38V33H27V29H14Z"/>
      </g>
      <path d="M16 19H28V15H32V12H36V9H38V18H33V23H26V26H16Z" fill="#38bdf8"/>
      <path d="M37 18H43V20H48V24H44V28H38V32H31V28H34V22Z" fill="#e0f2fe"/>
      <path d="M40 25H48V27H42V29H39Z" fill="#071d3c"/>
      <path d="M42 26H44V28H42Z" fill="white"/>
      <path d="M35 4H36V10H34Z" fill="#93c5fd"/>
      <rect x="41" y="16" width="4" height="3" fill="#67e8f9"/>
      <rect x="51" y="19" width="4" height="4" fill="#071d3c"/>
      <g fill="#60a5fa">
        <path d="M15 27H21V34H18V39H11V36H15Z">
          <animateTransform attributeName="transform" type="rotate" values="-22 18 28;22 18 28;-22 18 28" dur=".42s" repeatCount="indefinite"/>
        </path>
        <path d="M30 28H36V36H40V39H32V35H30Z">
          <animateTransform attributeName="transform" type="rotate" values="22 33 28;-22 33 28;22 33 28" dur=".42s" repeatCount="indefinite"/>
        </path>
      </g>
    </g>'''


def render(calendar, username, dark=True, demo=False):
    weeks = calendar['weeks']
    if not weeks or len(weeks) > 54:
        raise ValueError('Calendário vazio ou fora do limite de 54 semanas.')
    cells = []
    for col, week in enumerate(weeks):
        for day in week['contributionDays']:
            row = int(day['weekday'])
            count = int(day['contributionCount'])
            if row not in range(7) or count < 0:
                raise ValueError('Dia inválido no calendário.')
            cells.append((col, row, day))
    if not cells:
        raise ValueError('Nenhum dia retornado.')
    route = sorted(cells, key=lambda c: (c[1], c[0] if c[1] % 2 == 0 else -c[0]))
    step, left, top = 16, 56, 85
    width, height = max(520, len(weeks) * step + 110), 254
    duration = 72
    colors = (['#182637', '#123d67', '#1763a5', '#2399dc', '#7dd3fc'] if dark
              else ['#e5edf5', '#bfdbfe', '#60a5fa', '#2563eb', '#1e3a8a'])
    levels = dict(zip(['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE',
                      'THIRD_QUARTILE', 'FOURTH_QUARTILE'], colors))
    bg, fg, muted = ('#0d1117', '#dbeafe', '#8aa0b8') if dark else ('#ffffff', '#172554', '#526780')
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
    <title>Lobo das contribuições de {html.escape(username)}</title>
    <desc>Calendário do GitHub com um lobo azul animado. As cores representam contribuições; os brilhos são decorativos.</desc>
    <style>text{{font-family:Arial,sans-serif}} @media(prefers-reduced-motion:reduce){{.moving,.spark{{display:none}}}}</style>
    <rect width="100%" height="100%" rx="12" fill="{bg}"/>
    <text x="28" y="32" fill="{fg}" font-size="15" font-weight="bold">{html.escape(username)} / contribuições</text>
    <text x="28" y="53" fill="{muted}" font-size="11">{'PRÉVIA • DADOS FICTÍCIOS' if demo else str(calendar['totalContributions']) + ' contribuições no período retornado pelo GitHub'}</text>''']
    for row, label in [(1, 'Seg'), (3, 'Qua'), (5, 'Sex')]:
        parts.append(f'<text x="23" y="{top + row * step + 10}" font-size="10" fill="{muted}">{label}</text>')
    for i, (col, row, day) in enumerate(route):
        x, y = left + col * step, top + row * step
        color = levels.get(day['contributionLevel'], colors[0])
        title = html.escape(f"{day['date']}: {day['contributionCount']} contribuições")
        parts.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="2" fill="{color}"><title>{title}</title></rect>')
        arrival = .94 * i / max(1, len(route) - 1)
        # Same absolute timeline as the wolf: highlight only after its arrival.
        end = min(.999, arrival + .012)
        if i == 0:
            times, values = f'0;{end:.6f};1', '.85;0;0'
        else:
            times, values = f'0;{arrival:.6f};{end:.6f};1', '0;.85;0;0'
        parts.append(f'<rect class="spark" x="{x}" y="{y}" width="12" height="12" rx="2" fill="#67e8f9" opacity="0"><animate attributeName="opacity" values="{values}" keyTimes="{times}" calcMode="discrete" dur="{duration}s" repeatCount="indefinite"/></rect>')
    positions = [f'{left + c * step + 6} {top + r * step + 6}' for c, r, _ in route]
    times = [f'{.94 * i / max(1, len(route)-1):.6f}' for i in range(len(route))]
    positions.append(positions[-1])
    times.append('1')
    faces = ['1 1' if r % 2 == 0 else '-1 1' for _, r, _ in route]
    faces.append(faces[-1])
    parts.append(f'''<g class="moving" transform="translate({positions[0]})">
      <animateTransform attributeName="transform" type="translate" values="{';'.join(positions)}" keyTimes="{';'.join(times)}" dur="{duration}s" repeatCount="indefinite"/>
      <g><animateTransform attributeName="transform" type="scale" values="{';'.join(faces)}" keyTimes="{';'.join(times)}" calcMode="discrete" dur="{duration}s" repeatCount="indefinite"/>
      {wolf()}</g></g>''')
    parts.append(f'<text x="28" y="230" font-size="10" fill="{muted}">Cores = contribuições · brilho = passagem do lobo</text>')
    for i, color in enumerate(colors):
        parts.append(f'<rect x="{width-120+i*17}" y="220" width="12" height="12" rx="2" fill="{color}"/>')
    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', default=os.environ.get('PROFILE_USER', 'FelipeAViola'))
    parser.add_argument('--output', default='dist')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args()
    calendar = demo_calendar() if args.demo else fetch_calendar(args.user)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    # Preserve existing README URLs so installation needs no README replacement.
    for dark, name in [(False, 'github-contribution-grid-snake.svg'),
                       (True, 'github-contribution-grid-snake-dark.svg')]:
        (out / name).write_text(render(calendar, args.user, dark, args.demo), encoding='utf-8')
    print('Dois SVGs gerados' + (' com dados fictícios de prévia.' if args.demo else ' com dados do GitHub.'))


if __name__ == '__main__':
    main()
