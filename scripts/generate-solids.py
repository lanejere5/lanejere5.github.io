"""Draw the five Platonic solids as small hand-etched sketches for the CV section breaks.

Run: python3 scripts/generate-solids.py   (writes public/solids/*.svg)

The SVGs are used as CSS masks, so only shape and opacity matter; the page
colours them with the text colour.
"""
import itertools
import math
import re
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


# ---------- spinning animation ----------
#
# Each solid spins about one of its own symmetry axes, so a short run of frames
# loops seamlessly. Frames are stacked in one SVG and switched with SMIL, which
# browsers play even when the SVG is used as a CSS mask.

SPIN_TILT = 0.45          # radians the top is tipped toward the viewer
SPIN_STEP = 2.5           # degrees per frame
SPIN_SPEED = 12           # degrees per second

SPIN = {
    # name: (symmetry axis, order of rotational symmetry about it, tilt)
    'cube': ((0, 0, 1), 4, SPIN_TILT),
    'octahedron': ((0, 0, 1), 4, SPIN_TILT),
    'tetrahedron': ((1, 1, 1), 3, 1.2),                 # look down on the apex
    'dodecahedron': (None, 5, SPIN_TILT),               # through a face, found below
    'icosahedron': ((0, 1, PHI), 5, SPIN_TILT),
}


def align_to_y(axis):
    """Rotation matrix taking the unit vector `axis` to +y (Rodrigues)."""
    a = norm(axis)
    y = (0.0, 1.0, 0.0)
    v = cross(a, y)
    c = dot(a, y)
    if dot(v, v) < 1e-12:
        return ((1, 0, 0), (0, 1, 0), (0, 0, 1)) if c > 0 else ((1, 0, 0), (0, -1, 0), (0, 0, -1))
    k = 1 / (1 + c)
    vx, vy, vz = v
    return ((1 - k*(vy*vy + vz*vz), k*vx*vy - vz, k*vx*vz + vy),
            (k*vx*vy + vz, 1 - k*(vx*vx + vz*vz), k*vy*vz - vx),
            (k*vx*vz - vy, k*vy*vz + vx, 1 - k*(vx*vx + vy*vy)))


def apply(m, v):
    return tuple(dot(row, v) for row in m)


def spin_frame(name, align, theta, tilt, cx, cy, size):
    """One view of the solid. Strokes are seeded per edge and per face so they hold steady between frames."""
    vs0 = vertices(name)
    r0 = max(math.sqrt(dot(v, v)) for v in vs0)
    c, s_ = math.cos(theta), math.sin(theta)
    ct, st = math.cos(tilt), math.sin(tilt)
    vs = []
    for v in vs0:
        x, y, z = apply(align, mul(v, 1 / r0))
        x, z = c*x + s_*z, -s_*x + c*z
        y, z = ct*y - st*z, st*y + ct*z
        vs.append((x, y, z))
    proj = [(cx + x*size, cy - y*size) for x, y, _ in vs]
    light = norm(LIGHT)

    visible_edges, hidden_edges, hatches = set(), set(), []
    for idx, n in faces(vs):
        edges = {tuple(sorted((idx[i], idx[(i+1) % len(idx)]))) for i in range(len(idx))}
        if n[2] > 1e-6:
            visible_edges |= edges
            shade = dot(n, light)
            poly = [proj[m] for m in idx]
            rng = random.Random(f'{name}-face-{sorted(idx)}')
            if shade < 0.55:
                spacing = 2.2 + 3.4 * max(shade + 0.3, 0)
                hatches += hatch(rng, poly, math.radians(-50 + rng.uniform(-8, 8)), spacing, 0.06)
            if shade < -0.05:
                hatches += hatch(rng, poly, math.radians(20 + rng.uniform(-8, 8)), 2.8, 0.1)
        else:
            hidden_edges |= edges
    hidden_edges -= visible_edges

    def edge_rng(a, b):
        return random.Random(f'{name}-edge-{a}-{b}')

    parts = []
    for a, b in sorted(hidden_edges):
        parts.append(f'<path d="{wobbly(edge_rng(a, b), proj[a], proj[b], 0.3, 0.5)}" stroke-width="0.9" '
                     f'stroke-dasharray="1.2 2.2" opacity="0.45"/>')
    for d in hatches:
        parts.append(f'<path d="{d}" stroke-width="0.65" opacity="0.85"/>')
    for a, b in sorted(visible_edges):
        parts.append(f'<path d="{wobbly(edge_rng(a, b), proj[a], proj[b], 0.45, 1.4)}" stroke-width="1.7"/>')
    # One decimal place is plenty at this size and keeps the files small.
    return [re.sub(r'(\d\.\d)\d+', r'\1', p) for p in parts]


def spin_svgs(name):
    """Return (still, animated) SVG documents for a solid."""
    axis, order, tilt = SPIN[name]
    if axis is None:                                    # dodecahedron: axis through a face centre
        axis = faces(vertices(name))[0][1]
    align = align_to_y(axis)
    period = 360 / order
    frames = round(period / SPIN_STEP)
    dur = period / SPIN_SPEED
    # Start a third of the way round so the still frame shows the solid at an angle.
    views = [spin_frame(name, align, math.radians(period * (i / frames + 1 / 3)), tilt, 50, 50, 40)
             for i in range(frames)]

    still = svg(views[0], 100, 100)
    groups = []
    for i, parts in enumerate(views):
        if i == 0:
            values, times = '1;0', f'0;{1 / frames:.4f}'
        else:
            values, times = '0;1;0' if i < frames - 1 else '0;1', (
                f'0;{i / frames:.4f};{(i + 1) / frames:.4f}' if i < frames - 1 else f'0;{i / frames:.4f}')
        anim = (f'<animate attributeName="opacity" values="{values}" keyTimes="{times}" '
                f'calcMode="discrete" dur="{dur:g}s" repeatCount="indefinite"/>')
        groups.append(f'<g opacity="{1 if i == 0 else 0}">{anim}\n  ' + '\n  '.join(parts) + '\n  </g>')
    animated = svg(groups, 100, 100)
    return still, animated


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
    for name in SPIN:
        still, animated = spin_svgs(name)
        (OUT / f'{name}.svg').write_text(still)
        (OUT / f'{name}-spin.svg').write_text(animated)

    # Favicon: the exact dodecahedron drawing from the CV, on the page background.
    parts = draw('dodecahedron', SOLIDS['dodecahedron'], 50, 50, 40, seed=4)
    # Colours are the site's themes (src/styles/global.css), inverted so the icon
    # stands out against the browser chrome: dark tile in light mode, light tile in dark.
    style = ('<style>rect{fill:#131312}g{stroke:#f0eee9}'
             '@media (prefers-color-scheme:dark){rect{fill:#fbf8f2}g{stroke:#1d1a15}}</style>')
    favicon = svg(parts, 100, 100).replace(' stroke="#000"', '').replace(
        '  <g fill', f'  {style}\n  <rect width="100" height="100" rx="20"/>\n  <g fill', 1)
    (OUT.parent / 'favicon.svg').write_text(favicon)
    print('wrote', ', '.join(sorted(p.name for p in OUT.glob('*.svg'))))
