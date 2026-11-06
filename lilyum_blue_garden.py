import sys, os, math
import numpy as np
import pygame

W, H = 720, 1280
FPS = 60
T_STEM = 4.0
T_B0, T_B1 = 5.0, 15.0
LOOP_AT = 0
BG = (4, 2, 10)
S = W / 720.0

rng = np.random.default_rng(11)
gx, gy = W / 2, H * 0.82


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def midrib(L, a0, curl, K=40):
    us = np.linspace(0, 1, K + 1)
    al = a0 + curl * us ** 1.6
    ds = L / K
    r = np.concatenate([[0], np.cumsum(np.sin(al[1:])) * ds])
    h = np.concatenate([[0], np.cumsum(np.cos(al[1:])) * ds])
    return us, r, h


# ---------------------------------------------------------------- petals (BLUE)
def make_petals(NP, k):
    out = []
    for i in range(6):
        outer = (i % 2 == 0)
        pu = rng.random(NP) ** 0.85
        pv = rng.uniform(-1, 1, NP)
        prof = np.sin(np.pi * pu ** 0.7) ** 0.9
        keep = np.abs(pv) <= 1
        stops = np.array([0, .35, .7, 1])
        # deep royal blue at the throat -> cornflower -> sky -> icy lavender tip
        base = np.stack([
            np.interp(pu, stops, [40, 75, 135, 205]),
            np.interp(pu, stops, [70, 125, 185, 215]),
            np.interp(pu, stops, [200, 245, 255, 255]),
        ], axis=1)

        mid = (np.abs(pv) < 0.07) & (pu < 0.55)
        base[mid] = (200, 230, 255)                      # pale glowing midrib
        spot = (rng.random(NP) < 0.10) & (pu < 0.6) & (np.abs(pv) < 0.75) & ~mid
        base[spot] = (45, 35, 160)                       # deep indigo freckles
        edge = np.abs(pv) > 0.88
        base[edge] *= 1.08
        base *= (0.82 + 0.35 * rng.random((NP, 1)))
        out.append(dict(
            phi=math.radians(i * 60 + 8), L=(300 if outer else 280) * S * k,
            Wm=(64 if outer else 72) * S * k, ac=0.10 if outer else 0.05,
            ao=1.05 if outer else 0.82, curl=0.95 if outer else 0.75,
            pu=pu, pv=pv, prof=prof, base=base, keep=keep))
    return out


# ---------------------------------------------------------------- leaves (GREEN, unchanged colours)
def make_leaves(k, specs):
    leaves = []
    for (s0, Lf, side) in specs:
        n = int(900 * max(k, 0.55))
        u = rng.random(n) ** 0.9
        v = rng.uniform(-1, 1, n)
        prof = np.sin(np.pi * u ** 0.8) ** 0.8
        col = np.stack([lerp(40, 140, u), lerp(160, 235, u), lerp(100, 140, u)], axis=1)
        col[np.abs(v) < 0.08] = (190, 240, 170)
        col *= (0.8 + 0.4 * rng.random((n, 1)))
        leaves.append(dict(s0=s0, L=Lf * S * k, side=side, u=u, v=v, prof=prof, col=col))
    return leaves


# ---------------------------------------------------------------- one plant
def make_plant(dx, hs, k, delay, lean, wig, spin, psi0, ph, NP, NS, NF, specs):
    st_s = rng.random(NS)
    st_dx = rng.normal(0, 1, NS) * (3.2 * S * k) * (1 - 0.5 * st_s)
    st_col = np.stack([lerp(40, 120, st_s), lerp(150, 215, st_s), lerp(95, 120, st_s)], axis=1)
    st_col *= (0.8 + 0.4 * rng.random((NS, 1)))

    f_ph = rng.random(NF) * 6.28
    pal = np.array([[140, 200, 255], [200, 175, 255], [255, 175, 215]], float)
    f_col = pal[np.clip((f_ph / 2.1).astype(int), 0, 2)]

    NSP = int(70 * max(k, 0.6))
    return dict(
        x0=gx + dx * S, hs=hs * S, k=k, delay=delay, lean=lean * S, wig=wig,
        spin=spin, psi0=psi0, ph=ph,
        petals=make_petals(NP, k), leaves=make_leaves(k, specs),
        st_s=st_s, st_dx=st_dx, st_col=st_col,
        f_off=rng.random(NF), f_ph=f_ph, f_col=f_col,
        f_dr=rng.uniform(-80, 80, NF) * S * k, f_sp=rng.uniform(0.05, 0.12, NF),
        sp_x=rng.normal(0, 1, NSP) * 130 * S * k,
        sp_y=rng.uniform(-0.6, 1.3, NSP) * 150 * S * k,
        sp_ph=rng.random(NSP) * 6.28, sp_f=rng.uniform(1.5, 4.5, NSP),
        stam=[dict(an=rng.normal(0, 1, (35, 2))) for _ in range(6)],
    )


PLANTS = [
    # main (centre) flower
    make_plant(dx=0, hs=380, k=1.0, delay=0.0, lean=0, wig=1, spin=0.22, psi0=0.25, ph=0.0,
               NP=2300, NS=3200, NF=140,
               specs=[(0.10, 190, 1), (0.24, 175, -1), (0.40, 150, 1), (0.56, 120, -1)]),
    # left flower
    make_plant(dx=-175, hs=285, k=0.58, delay=0.9, lean=-25, wig=-1, spin=-0.18, psi0=1.2, ph=1.7,
               NP=1500, NS=1900, NF=70,
               specs=[(0.14, 190, 1), (0.34, 160, -1), (0.52, 130, 1)]),
    # right flower
    make_plant(dx=185, hs=235, k=0.50, delay=1.5, lean=20, wig=1, spin=0.26, psi0=2.1, ph=3.4,
               NP=1400, NS=1700, NF=60,
               specs=[(0.16, 180, -1), (0.36, 150, 1), (0.54, 120, -1)]),
]

# ---------------------------------------------------------------- soil / dust
NG = 5000
so_dx = rng.uniform(-340, 340, NG) * S
mound = (1 - (so_dx / (340 * S)) ** 2) * 55 * S
so_y = gy - mound * rng.random(NG) ** 0.5 + rng.normal(0, 1.5, NG)
so_col = np.stack([lerp(30, 90, rng.random(NG)), lerp(130, 210, rng.random(NG)), lerp(40, 100, rng.random(NG))], axis=1)

ND = 450
d_x = rng.random(ND) * W
d_y = rng.random(ND) * H
d_sp = rng.uniform(6, 22, ND) * S
d_ph = rng.random(ND) * 6.28
d_f = rng.uniform(1, 4, ND)


def stem_x(p, s, t):
    sway = 10 * S * p['k'] * math.sin(0.9 * t + p['ph'])
    return (p['x0'] + p['lean'] * s ** 1.5
            + p['wig'] * 30 * S * p['k'] * np.sin(2.2 * s) + sway * s ** 2)


def stem_y(p, s):
    return gy - s * p['hs']


def render(t, buf):
    P, Zs, C = [], [], []

    def add(x, y, z, col):
        P.append(np.stack([x, y], 1))
        Zs.append(np.broadcast_to(z, x.shape).astype(float))
        C.append(col)

    # twinkling background dust (no rotating ring any more)
    tw = 0.35 + 0.65 * (np.sin(t * d_f + d_ph) > 0.2)
    yy = (d_y - t * d_sp) % H
    add(d_x, yy, -1000, np.stack([255 * tw, 200 * tw, 235 * tw], 1) * 0.55)

    add(so_dx + gx, so_y, -500, so_col * 0.8)

    for p in PLANTS:
        k = p['k']
        tl = t - p['delay']
        if tl <= 0:
            continue
        g = smooth(tl / T_STEM)
        e = smooth((tl - T_B0) / (T_B1 - T_B0))
        rev = float(smooth((tl - T_STEM + 0.3) / 1.6))

        hx, hy = float(stem_x(p, 1.0, t)), float(stem_y(p, 1.0))

        # ---- stalk (green)
        m = p['st_s'] <= g
        if m.any():
            s = p['st_s'][m]
            add(stem_x(p, s, t) + p['st_dx'][m], stem_y(p, s), -100, p['st_col'][m])

        # ---- leaves (green)
        for lf in p['leaves']:
            lg = float(np.clip((g - lf['s0']) * 2.5, 0, 1))
            if lg <= 0.01:
                continue
            L = lf['L'] * lg
            us, r, h = midrib(L, 0.85, 1.1)
            u, v = lf['u'], lf['v']
            rr, hh = np.interp(u, us, r), np.interp(u, us, h)
            wid = 15 * S * k * lf['prof'] * lg
            bx, by = float(stem_x(p, lf['s0'], t)), float(stem_y(p, lf['s0']))
            sway = math.sin(t * 1.2 + lf['s0'] * 5 + p['ph']) * 0.03
            x = bx + lf['side'] * (rr + v * wid * 0.35) + sway * hh * lf['side']
            y = by - hh + v * wid
            add(x, y, -90, lf['col'])

        if rev > 0.01:
            psi = p['psi0'] + t * p['spin']
            tau = 0.5
            cp, sp = math.cos(psi), math.sin(psi)
            ct, st = math.cos(tau), math.sin(tau)
            sway_t = math.sin(t * 0.8 + p['ph']) * 0.02

            # ---- petals (blue)
            for pt in p['petals']:
                Ls = pt['L'] * (0.45 + 0.55 * e) * (0.35 + 0.65 * rev)
                a0 = lerp(pt['ac'], pt['ao'], e)
                curl = (0.12 + 0.88 * e) * pt['curl']
                us, r, h = midrib(Ls, a0, curl)
                pu, pv = pt['pu'], pt['pv']
                mk = (pu <= rev) & pt['keep']
                u, v, pr = pu[mk], pv[mk], pt['prof'][mk]
                rr, hh = np.interp(u, us, r), np.interp(u, us, h)
                wid = pt['Wm'] * (0.55 + 0.45 * e) * pr * (0.35 + 0.65 * rev)
                ph = pt['phi']
                X = rr * math.cos(ph) - v * wid * math.sin(ph)
                Z = rr * math.sin(ph) + v * wid * math.cos(ph)
                Y = hh + (v ** 2) * wid * (0.30 * (1 - e) - 0.25 * e)
                Xp = X * cp + Z * sp
                Zp = -X * sp + Z * cp
                sy = Y * ct - Zp * st
                shade = 0.55 + 0.45 * np.clip(Zp / pt['L'] * 0.8 + 0.5, 0, 1)
                col = pt['base'][mk].copy()
                # young bud: faint cool green-teal at the tips, fades as it blooms
                tint = ((1 - e) * np.clip(u * 1.3, 0, 1) * 0.45)[:, None]
                col = col * (1 - tint) + np.array([120, 200, 175]) * tint
                add(hx + Xp + sway_t * sy, hy - sy, Zp, col * shade[:, None])

            # ---- stamens (soft gold so they glow against the blue)
            if e > 0.28:
                sr = float(smooth((e - 0.28) / 0.4))
                for k6, sdat in enumerate(p['stam']):
                    Ls = 215 * S * k * (0.4 + 0.6 * e) * sr
                    us, r, h = midrib(Ls, lerp(0.15, 0.62, e), 0.55 * e)
                    u = rng.random(45)
                    rr, hh = np.interp(u, us, r), np.interp(u, us, h)
                    ph = math.radians(k6 * 60 + 38)
                    X, Z, Y = rr * math.cos(ph), rr * math.sin(ph), hh
                    Xp = X * cp + Z * sp
                    Zp = -X * sp + Z * cp
                    sy = Y * ct - Zp * st
                    add(hx + Xp, hy - sy, Zp + 5,
                        np.broadcast_to(np.array([235, 240, 255]), (45, 3)).astype(float))

                    tx, tz, ty = r[-1] * math.cos(ph), r[-1] * math.sin(ph), h[-1]
                    txp = tx * cp + tz * sp
                    tzp = -tx * sp + tz * cp
                    tsy = ty * ct - tzp * st
                    an = sdat['an'] * 5 * S * k
                    ac = np.broadcast_to(np.array([255, 210, 110]), (35, 3)).astype(float) * (0.8 + 0.4 * rng.random((35, 1)))
                    add(hx + txp + an[:, 0] * 1.6, hy - tsy + an[:, 1] * 0.7, tzp + 6, ac)

        if e > 0.5:
            # ---- romantic sparkles floating gently around the bloom
            sa = float(smooth((e - 0.5) / 0.5))
            twk = (np.sin(t * p['sp_f'] + p['sp_ph']) * 0.5 + 0.5) ** 2
            sx = hx + p['sp_x'] + np.sin(t * 0.5 + p['sp_ph']) * 6 * S
            sy2 = hy - 70 * S * k - p['sp_y'] + np.cos(t * 0.4 + p['sp_ph']) * 5 * S
            add(sx, sy2, 400, np.outer(twk * sa, np.array([200, 225, 255])))

        if e > 0.6:
            # ---- drifting blue / lilac / blush petals
            fa = float(smooth((e - 0.6) / 0.4))
            q = (t * p['f_sp'] + p['f_off']) % 1.0
            fx = hx + p['f_dr'] * q + np.sin(q * 7 + p['f_ph']) * 25 * S * k
            fy = (hy - 110 * S * k) + q * (gy - hy + 90 * S * k)
            fade = (1 - q) * fa
            add(fx, fy, 300, p['f_col'] * fade[:, None])

    x = np.concatenate([p[:, 0] for p in P])
    y = np.concatenate([p[:, 1] for p in P])
    z = np.concatenate(Zs)
    c = np.concatenate(C)
    o = np.argsort(z, kind='stable')
    x, y, c = x[o], y[o], np.clip(c[o], 0, 255).astype(np.uint8)
    ix, iy = x.astype(int), y.astype(int)
    ok = (ix >= 0) & (ix < W - 2) & (iy >= 0) & (iy < H - 2)
    ix, iy, c = ix[ok], iy[ok], c[ok]
    buf[:] = BG
    buf[ix, iy] = c
    buf[ix + 1, iy] = c
    buf[ix, iy + 1] = c


def glow(screen):
    small = pygame.transform.smoothscale(screen, (W // 10, H // 10))
    big = pygame.transform.smoothscale(small, (W, H))
    screen.blit(big, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def main():
    pygame.init()

    if len(sys.argv) >= 4 and sys.argv[1] == '--frame':
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.display.init()
        screen = pygame.display.set_mode((W, H))
        buf = np.zeros((W, H, 3), np.uint8)
        render(float(sys.argv[2]), buf)
        pygame.surfarray.blit_array(screen, buf)
        glow(screen)
        pygame.image.save(screen, sys.argv[3])
        return
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Blue Lily Garden")
    clock = pygame.time.Clock()
    buf = np.zeros((W, H, 3), np.uint8)
    t, paused = 0.0, False
    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    t = 0.0
                if ev.key == pygame.K_SPACE:
                    paused = not paused
        if not paused:
            t += dt
            if LOOP_AT and t > LOOP_AT:
                t = 0.0
        render(t, buf)
        pygame.surfarray.blit_array(screen, buf)
        glow(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
