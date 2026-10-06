"""Draw the five Platonic solids as small hand-etched sketches for the CV section breaks.

Run: python3 scripts/generate-solids.py   (writes public/solids/*.svg)

The SVGs are used as CSS masks, so only shape and opacity matter; the page
colours them with the text colour.
"""
import itertools
import math
import random
from pathlib import Path

PHI = (1 + 5 ** 0.5) / 2
OUT = Path(__file__).resolve().parent.parent / 'public' / 'solids'
LIGHT = (-0.5, 0.65, 0.58)  # upper left, toward the viewer


# ---------- vectors ----------

def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])
def norm(a):
    n = math.sqrt(dot(a, a))
    return tuple(x / n for x in a)


# ---------- solids ----------

def vertices(name):
    if name == 'tetrahedron':
        return [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    if name == 'cube':
        return list(itertools.product((-1, 1), repeat=3))
    if name == 'octahedron':
        return [v for i in range(3) for s in (-1, 1) for v in [tuple(s if j == i else 0 for j in range(3))]]
    if name == 'icosahedron':
        vs = []
        for a, b in itertools.product((-1, 1), repeat=2):
            vs += [(0, a, b * PHI), (a, b * PHI, 0), (b * PHI, 0, a)]
        return vs
    if name == 'dodecahedron':
        vs = list(itertools.product((-1, 1), repeat=3))
        for a, b in itertools.product((-1, 1), repeat=2):
            vs += [(0, a / PHI, b * PHI), (a / PHI, b * PHI, 0), (b * PHI, 0, a / PHI)]
        return vs
    raise ValueError(name)


def faces(vs):
    """Faces of a convex polyhedron as vertex-index lists, ordered counter-clockwise from outside."""
    found = {}
    for i, j, k in itertools.combinations(range(len(vs)), 3):
        n = cross(sub(vs[j], vs[i]), sub(vs[k], vs[i]))
        if dot(n, n) < 1e-9:
            continue
        n = norm(n)
        d = dot(n, vs[i])
        side = [dot(n, v) - d for v in vs]
        if all(s <= 1e-6 for s in side):
            pass
        elif all(s >= -1e-6 for s in side):
            n, d = mul(n, -1), -d
        else:
            continue
        on = tuple(sorted(m for m, v in enumerate(vs) if abs(dot(n, v) - d) < 1e-6))
        if on in found:
            continue
        c = mul(tuple(map(sum, zip(*(vs[m] for m in on)))), 1 / len(on))
        u = norm(sub(vs[on[0]], c))
        w = cross(n, u)
        ordered = sorted(on, key=lambda m: math.atan2(dot(sub(vs[m], c), w), dot(sub(vs[m], c), u)))
        found[on] = (ordered, n)
    return list(found.values())


def rotate(v, yaw, pitch, roll):
    x, y, z = v
    c, s = math.cos(yaw), math.sin(yaw)
    x, z = c*x + s*z, -s*x + c*z
    c, s = math.cos(pitch), math.sin(pitch)
    y, z = c*y - s*z, s*y + c*z
    c, s = math.cos(roll), math.sin(roll)
    x, y = c*x - s*y, s*x + c*y
    return (x, y, z)


# ---------- hand-drawn strokes ----------

def wobbly(rng, p, q, amp, overshoot):
    """A slightly uneven line from p to q, extended a little past each end like a quick pen stroke."""
    d = sub(q, p)
    length = math.hypot(*d) or 1
    t_dir = (d[0] / length, d[1] / length)
    nrm = (-t_dir[1], t_dir[0])
    a = rng.uniform(0.2, 1) * overshoot
    b = rng.uniform(0.2, 1) * overshoot
    p = (p[0] - t_dir[0]*a, p[1] - t_dir[1]*a)
    q = (q[0] + t_dir[0]*b, q[1] + t_dir[1]*b)
    phase, freq = rng.uniform(0, 6.3), rng.uniform(0.8, 1.6)
    pts = []
    steps = max(3, int(length / 6))
    for i in range(steps + 1):
        t = i / steps
        off = amp * (math.sin(phase + freq * math.pi * t) + rng.uniform(-0.35, 0.35)) * math.sin(math.pi * t)
        pts.append((p[0] + (q[0]-p[0])*t + nrm[0]*off, p[1] + (q[1]-p[1])*t + nrm[1]*off))
    return 'M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in pts)


def clip(p, d, poly):
    """Clip the infinite line p + t*d to a convex polygon (Cyrus-Beck). Returns endpoints or None."""
    t0, t1 = -1e9, 1e9
    n = len(poly)
    area = sum(poly[i][0]*poly[(i+1) % n][1] - poly[(i+1) % n][0]*poly[i][1] for i in range(n))
    for i in range(n):
        a, b = poly[i], poly[(i+1) % n]
        e = (b[0]-a[0], b[1]-a[1])
        inward = (-e[1], e[0]) if area > 0 else (e[1], -e[0])
        num = (p[0]-a[0])*inward[0] + (p[1]-a[1])*inward[1]
        den = d[0]*inward[0] + d[1]*inward[1]
        if abs(den) < 1e-12:
            if num < 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t1 - t0 < 1e-6:
        return None
    return (p[0]+d[0]*t0, p[1]+d[1]*t0), (p[0]+d[0]*t1, p[1]+d[1]*t1)


def hatch(rng, poly, angle, spacing, inset):
    """Parallel hatch strokes across a projected face, kept a little inside its edges."""
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    shrunk = [(cx + (x-cx)*(1-inset), cy + (y-cy)*(1-inset)) for x, y in poly]
    d = (math.cos(angle), math.sin(angle))
    nrm = (-d[1], d[0])
    reach = max(math.hypot(x-cx, y-cy) for x, y in poly)
    out = []
    k = -reach
    while k <= reach:
        p = (cx + nrm[0]*k, cy + nrm[1]*k)
        seg = clip(p, d, shrunk)
        if seg:
            out.append(wobbly(rng, seg[0], seg[1], amp=0.25, overshoot=0.6))
        k += spacing * rng.uniform(0.85, 1.15)
    return out


# ---------- drawing ----------

def draw(name, rot, cx, cy, size, seed):
    rng = random.Random(seed)
    vs0 = vertices(name)
    r0 = max(math.sqrt(dot(v, v)) for v in vs0)
    vs = [rotate(mul(v, 1 / r0), *rot) for v in vs0]
    fs = faces(vs)
    proj = [(cx + x*size, cy - y*size) for x, y, _ in vs]
    light = norm(LIGHT)

    visible_edges, hidden_edges, hatches = set(), set(), []
    for idx, n in fs:
        edges = {tuple(sorted((idx[i], idx[(i+1) % len(idx)]))) for i in range(len(idx))}
        if n[2] > 1e-6:
            visible_edges |= edges
            shade = dot(n, light)                       # 1 = facing the light
            poly = [proj[m] for m in idx]
            if shade < 0.55:
                spacing = 2.2 + 3.4 * max(shade + 0.3, 0)
                hatches += hatch(rng, poly, math.radians(-50 + rng.uniform(-8, 8)), spacing, 0.06)
            if shade < -0.05:
                hatches += hatch(rng, poly, math.radians(20 + rng.uniform(-8, 8)), 2.8, 0.1)
        else:
            hidden_edges |= edges
    hidden_edges -= visible_edges

    parts = []
    for a, b in sorted(hidden_edges):
        parts.append(f'<path d="{wobbly(rng, proj[a], proj[b], 0.3, 0.5)}" stroke-width="0.9" '
                     f'stroke-dasharray="1.2 2.2" opacity="0.45"/>')
    for d in hatches:
        parts.append(f'<path d="{d}" stroke-width="0.65" opacity="0.85"/>')
    for a, b in sorted(visible_edges):
        parts.append(f'<path d="{wobbly(rng, proj[a], proj[b], 0.45, 1.4)}" stroke-width="1.7"/>')
    return parts


def svg(parts, w, h):
    body = '\n  '.join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">\n'
            f'  <!-- Generated by scripts/generate-solids.py -->\n'
            f'  <g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">\n  {body}\n  </g>\n</svg>\n')


SOLIDS = {
    'tetrahedron': (0.8, -2.7, 0.0),
    'cube': (0.62, 0.48, 0.0),
    'octahedron': (0.40, 0.30, 0.12),
    'dodecahedron': (0.35, 0.42, 0.05),
    'icosahedron': (0.30, 0.38, 0.0),
}

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (name, rot) in enumerate(SOLIDS.items()):
        (OUT / f'{name}.svg').write_text(svg(draw(name, rot, 50, 50, 40, seed=i + 1), 100, 100))
    # Final break: dual pairs either side of the self-dual tetrahedron.
    layout = [('cube', 50), ('octahedron', 150), ('tetrahedron', 250),
              ('dodecahedron', 350), ('icosahedron', 450)]
    row = []
    for i, (name, x) in enumerate(layout):
        row += draw(name, SOLIDS[name], x, 50, 40, seed=i + 11)
    (OUT / 'all.svg').write_text(svg(row, 500, 100))

    # Favicon: the exact dodecahedron drawing from the CV, on the page background.
    parts = draw('dodecahedron', SOLIDS['dodecahedron'], 50, 50, 40, seed=4)
    # Colours are the site's themes (src/styles/global.css), inverted so the icon
    # stands out against the browser chrome: dark tile in light mode, light tile in dark.
    style = ('<style>rect{fill:#131312}g{stroke:#f0eee9}'
             '@media (prefers-color-scheme:dark){rect{fill:#f7f1e5}g{stroke:#1d1a15}}</style>')
    favicon = svg(parts, 100, 100).replace(' stroke="#000"', '').replace(
        '  <g fill', f'  {style}\n  <rect width="100" height="100" rx="20"/>\n  <g fill', 1)
    (OUT.parent / 'favicon.svg').write_text(favicon)
    print('wrote', ', '.join(sorted(p.name for p in OUT.glob('*.svg'))))
