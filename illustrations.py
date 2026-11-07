"""Flat, friendly illustrations for the AI curation page, drawn in SVG (no image files, nothing AI-generated).

Style: solid shapes, no outlines, dot eyes, open smiles, warm pastels on a cream ground.
Each scene() returns a self-contained <svg> string, 280 x 190.
"""

INK = "#3A2833"
CREAM = "#FFF4E6"
PLUM, PLUM_LT = "#C5679A", "#F3D3E3"
SAGE, SAGE_LT = "#6FA58C", "#D5EADF"
CORAL = "#EE7A64"
GOLD, GOLD_LT = "#E9B45A", "#F8E3B8"
NAVY = "#4D6A9A"
SKY = "#DDEBF5"
SKIN = ["#F5C9A6", "#E8A97E", "#C68660", "#8D5A3B"]
HAIR = ["#2F3A5A", "#3A2833", "#8A4B2A", "#1F1A22"]


def person(cx, base, s=1.0, skin=SKIN[0], hair=HAIR[0], shirt=PLUM, style="short", arms="up"):
    """One person from the chest up. base is the bottom of the shirt."""
    def P(x, y):  # scale around (cx, base)
        return f"{cx + x * s:.1f},{base + y * s:.1f}"

    def r(v):
        return f"{v * s:.1f}"

    out = []
    # arms go behind the shirt
    def arm(side, up):
        sx = cx + side * 26 * s
        sy = base - 50 * s
        if up:
            hx, hy = cx + side * 46 * s, base - 116 * s
        else:
            hx, hy = cx + side * 40 * s, base - 4 * s
        mx, my = sx + (hx - sx) * .32, sy + (hy - sy) * .32
        out.append(f"<line x1='{sx:.1f}' y1='{sy:.1f}' x2='{hx:.1f}' y2='{hy:.1f}' stroke='{skin}' "
                   f"stroke-width='{r(13)}' stroke-linecap='round'/>")
        out.append(f"<line x1='{sx:.1f}' y1='{sy:.1f}' x2='{mx:.1f}' y2='{my:.1f}' stroke='{shirt}' "
                   f"stroke-width='{r(17)}' stroke-linecap='round'/>")
        if up:
            out.append(f"<circle cx='{hx:.1f}' cy='{hy:.1f}' r='{r(9)}' fill='{skin}'/>")
    if arms in ("up", "left"):
        arm(-1, True)
    if arms in ("up", "right"):
        arm(1, True)
    if style == "long":  # hair behind the head
        out.append(f"<rect x='{cx - 28 * s:.1f}' y='{base - 122 * s:.1f}' width='{r(56)}' height='{r(64)}' "
                   f"rx='{r(26)}' fill='{hair}'/>")
    out.append(f"<rect x='{cx - 34 * s:.1f}' y='{base - 62 * s:.1f}' width='{r(68)}' height='{r(62)}' "
               f"rx='{r(22)}' fill='{shirt}'/>")
    out.append(f"<rect x='{cx - 7 * s:.1f}' y='{base - 76 * s:.1f}' width='{r(14)}' height='{r(18)}' fill='{skin}'/>")
    out.append(f"<circle cx='{cx + 22 * s:.1f}' cy='{base - 95 * s:.1f}' r='{r(5.5)}' fill='{skin}'/>")
    out.append(f"<circle cx='{cx:.1f}' cy='{base - 97 * s:.1f}' r='{r(24)}' fill='{skin}'/>")
    if style == "long":
        out.append(f"<path d='M{P(-25, -96)} Q{P(-22, -126)} {P(2, -124)} Q{P(26, -122)} {P(25, -100)} "
                   f"Q{P(8, -114)} {P(-8, -108)} Q{P(-18, -104)} {P(-25, -96)}Z' fill='{hair}'/>")
    elif style == "bun":
        out.append(f"<circle cx='{cx + 2 * s:.1f}' cy='{base - 128 * s:.1f}' r='{r(11)}' fill='{hair}'/>")
        out.append(f"<path d='M{P(-24, -98)} Q{P(-22, -124)} {P(1, -123)} Q{P(25, -122)} {P(24, -100)} "
                   f"Q{P(4, -112)} {P(-24, -98)}Z' fill='{hair}'/>")
    else:  # short, with a little swoop
        out.append(f"<path d='M{P(-24, -96)} Q{P(-26, -126)} {P(0, -125)} Q{P(28, -124)} {P(24, -98)} "
                   f"Q{P(20, -108)} {P(10, -110)} Q{P(-6, -106)} {P(-14, -112)} Q{P(-18, -102)} {P(-24, -96)}Z' "
                   f"fill='{hair}'/>")
    out.append(f"<circle cx='{cx - 8 * s:.1f}' cy='{base - 97 * s:.1f}' r='{r(2.6)}' fill='{INK}'/>")
    out.append(f"<circle cx='{cx + 9 * s:.1f}' cy='{base - 97 * s:.1f}' r='{r(2.6)}' fill='{INK}'/>")
    out.append(f"<path d='M{P(-8, -87)} Q{P(1, -76)} {P(10, -87)}Z' fill='{INK}'/>")
    out.append(f"<circle cx='{cx - 14 * s:.1f}' cy='{base - 89 * s:.1f}' r='{r(3.5)}' fill='{CORAL}' opacity='.35'/>")
    return "".join(out)


def robot(cx, cy, s=1.0, body=PLUM_LT, face=PLUM, eyes="dots"):
    """A small friendly robot head and body. cy is the center of the head."""
    def r(v):
        return f"{v * s:.1f}"
    o = [f"<line x1='{cx:.1f}' y1='{cy - 30 * s:.1f}' x2='{cx:.1f}' y2='{cy - 44 * s:.1f}' stroke='{face}' "
         f"stroke-width='{r(3)}' stroke-linecap='round'/>",
         f"<circle cx='{cx:.1f}' cy='{cy - 47 * s:.1f}' r='{r(5)}' fill='{GOLD}'/>",
         f"<rect x='{cx - 30 * s:.1f}' y='{cy + 26 * s:.1f}' width='{r(60)}' height='{r(40)}' rx='{r(14)}' fill='{body}'/>",
         f"<rect x='{cx - 38 * s:.1f}' y='{cy - 30 * s:.1f}' width='{r(76)}' height='{r(60)}' rx='{r(20)}' fill='{body}'/>",
         f"<rect x='{cx - 28 * s:.1f}' y='{cy - 20 * s:.1f}' width='{r(56)}' height='{r(40)}' rx='{r(14)}' fill='{face}'/>"]
    if eyes == "hearts":
        for dx in (-11, 11):
            x, y = cx + dx * s, cy - 4 * s
            o.append(f"<path d='M{x:.1f},{y + 6 * s:.1f} l{-6 * s:.1f},{-6 * s:.1f} a{3.4 * s:.1f},{3.4 * s:.1f} 0 0 1 "
                     f"{6 * s:.1f},{-4 * s:.1f} a{3.4 * s:.1f},{3.4 * s:.1f} 0 0 1 {6 * s:.1f},{4 * s:.1f}z' fill='#fff'/>")
    else:
        for dx in (-11, 11):
            o.append(f"<circle cx='{cx + dx * s:.1f}' cy='{cy - 4 * s:.1f}' r='{r(4.5)}' fill='#fff'/>")
    o.append(f"<path d='M{cx - 8 * s:.1f},{cy + 8 * s:.1f} Q{cx:.1f},{cy + 15 * s:.1f} {cx + 8 * s:.1f},{cy + 8 * s:.1f}' "
             f"stroke='#fff' stroke-width='{r(2.6)}' fill='none' stroke-linecap='round'/>")
    return "".join(o)


def needle(x, base, s=1.0, color=NAVY):
    """Space Needle silhouette."""
    def P(dx, dy):
        return f"{x + dx * s:.1f},{base + dy * s:.1f}"
    return (f"<path d='M{P(-9, 0)} L{P(-3, -70)} L{P(3, -70)} L{P(9, 0)}Z' fill='{color}'/>"
            f"<ellipse cx='{x:.1f}' cy='{base - 74 * s:.1f}' rx='{22 * s:.1f}' ry='{5 * s:.1f}' fill='{color}'/>"
            f"<path d='M{P(-14, -79)} Q{P(0, -90)} {P(14, -79)}Z' fill='{color}'/>"
            f"<line x1='{x:.1f}' y1='{base - 86 * s:.1f}' x2='{x:.1f}' y2='{base - 106 * s:.1f}' stroke='{color}' "
            f"stroke-width='{2.2 * s:.1f}' stroke-linecap='round'/>")


def mountain(x, base, w, h):
    """Rainier: a soft peak with a snowcap."""
    return (f"<path d='M{x - w / 2:.1f},{base} L{x:.1f},{base - h} L{x + w / 2:.1f},{base}Z' fill='#B9CBE0'/>"
            f"<path d='M{x - w * .16:.1f},{base - h * .68:.1f} L{x:.1f},{base - h} L{x + w * .16:.1f},{base - h * .68:.1f} "
            f"L{x + w * .06:.1f},{base - h * .74:.1f} L{x - w * .04:.1f},{base - h * .64:.1f}Z' fill='#fff'/>")


def heart(x, y, s=1.0, color=CORAL):
    return (f"<path d='M{x:.1f},{y + 7 * s:.1f} l{-8 * s:.1f},{-8 * s:.1f} a{4.6 * s:.1f},{4.6 * s:.1f} 0 0 1 {8 * s:.1f},"
            f"{-5.6 * s:.1f} a{4.6 * s:.1f},{4.6 * s:.1f} 0 0 1 {8 * s:.1f},{5.6 * s:.1f}z' fill='{color}'/>")


def sparkle(x, y, s=1.0, color=GOLD):
    return (f"<path d='M{x:.1f},{y - 8 * s:.1f} Q{x + 1.5 * s:.1f},{y - 1.5 * s:.1f} {x + 8 * s:.1f},{y:.1f} "
            f"Q{x + 1.5 * s:.1f},{y + 1.5 * s:.1f} {x:.1f},{y + 8 * s:.1f} Q{x - 1.5 * s:.1f},{y + 1.5 * s:.1f} "
            f"{x - 8 * s:.1f},{y:.1f} Q{x - 1.5 * s:.1f},{y - 1.5 * s:.1f} {x:.1f},{y - 8 * s:.1f}Z' fill='{color}'/>")


def row(x, y, w, dot=PLUM, line="#E6DCD3"):
    return (f"<circle cx='{x + 6}' cy='{y + 5}' r='5' fill='{dot}'/>"
            f"<rect x='{x + 16}' y='{y + 1}' width='{w}' height='8' rx='4' fill='{line}'/>")


def wrap(inner, bg=CREAM):
    return (f"<svg viewBox='0 0 280 190' xmlns='http://www.w3.org/2000/svg' role='img'>"
            f"<rect width='280' height='190' rx='22' fill='{bg}'/>{inner}</svg>")


def scene_pull():
    """1. Pulling a list of events from listing sites."""
    win = ("<rect x='22' y='30' width='150' height='128' rx='14' fill='#fff'/>"
           "<rect x='22' y='30' width='150' height='22' rx='11' fill='#F1E6DC'/>"
           "<circle cx='36' cy='41' r='4' fill='#EE7A64'/><circle cx='48' cy='41' r='4' fill='#E9B45A'/>"
           "<circle cx='60' cy='41' r='4' fill='#6FA58C'/>"
           + row(34, 64, 110) + row(34, 84, 90, SAGE) + row(34, 104, 120, GOLD) + row(34, 124, 80, NAVY)
           + row(34, 144, 100, CORAL))
    flying = ("<rect x='176' y='58' width='40' height='14' rx='7' fill='#fff'/>"
              "<rect x='186' y='80' width='34' height='14' rx='7' fill='#fff'/>")
    return wrap(win + flying + person(232, 190, .78, SKIN[1], HAIR[1], SAGE, "long", "left"))


def scene_parse():
    """2. A low-cost model tidies messy page text into event cards."""
    mess = "".join(f"<rect x='{x}' y='{y}' width='{w}' height='7' rx='3.5' fill='#E6DCD3' transform='rotate({a} {x} {y})'/>"
                   for x, y, w, a in [(20, 46, 58, -8), (28, 66, 44, 6), (18, 88, 62, -4), (30, 110, 40, 10),
                                      (22, 130, 54, -6)])
    cards = "".join(f"<rect x='196' y='{y}' width='66' height='26' rx='8' fill='#fff'/>"
                    f"<circle cx='208' cy='{y + 13}' r='5' fill='{c}'/><rect x='218' y='{y + 9}' width='36' height='7' "
                    f"rx='3.5' fill='#E6DCD3'/>" for y, c in [(42, PLUM), (76, SAGE), (110, GOLD)])
    arrow = "<path d='M88,98 L104,98 M98,92 L104,98 L98,104' stroke='#D7C6B8' stroke-width='4' stroke-linecap='round' fill='none'/>" \
            "<path d='M176,98 L190,98 M184,92 L190,98 L184,104' stroke='#D7C6B8' stroke-width='4' " \
            "stroke-linecap='round' fill='none'/>"
    tag = ("<rect x='108' y='150' width='64' height='22' rx='11' fill='#fff'/>"
           "<text x='140' y='165' text-anchor='middle' font-family='Figtree,sans-serif' font-size='11' "
           "font-weight='700' fill='#6FA58C'>low-cost</text>")
    return wrap(mess + arrow + cards + robot(140, 92, .78, SAGE_LT, SAGE) + tag)


def scene_match():
    """3. A stronger model picks the events that mean something."""
    keep = "".join(f"<rect x='20' y='{y}' width='70' height='26' rx='8' fill='#fff'/>"
                   + heart(36, y + 10, .7) + f"<rect x='48' y='{y + 9}' width='34' height='7' rx='3.5' fill='#E6DCD3'/>"
                   for y in (52, 86, 120))
    toss = ("<rect x='196' y='118' width='66' height='26' rx='8' fill='#fff' opacity='.55' transform='rotate(8 229 131)'/>"
            "<path d='M206,126 l10,10 M216,126 l-10,10' stroke='#EE7A64' stroke-width='3' stroke-linecap='round' "
            "transform='rotate(8 229 131)'/>")
    sp = sparkle(212, 44, 1.1) + sparkle(244, 70, .7, PLUM) + sparkle(98, 34, .6)
    return wrap(keep + toss + sp + robot(150, 88, 1.0, PLUM_LT, PLUM, "hearts"))


def scene_loop():
    """4. The team votes, and the AI learns."""
    loop = ("<path d='M60,52 A90,64 0 0 1 220,52' stroke='#E3D3C6' stroke-width='5' fill='none' stroke-linecap='round' "
            "stroke-dasharray='2 10'/>"
            "<path d='M212,42 L222,53 L208,58' stroke='#E3D3C6' stroke-width='5' fill='none' stroke-linecap='round' "
            "stroke-linejoin='round'/>")
    thumbs = ("<g transform='translate(18 18)'><rect width='40' height='32' rx='12' fill='#fff'/>"
              "<path d='M13,22 L13,14 L18,14 L22,6 Q26,6 25,12 L31,12 Q33,13 32,16 L30,22Z' fill='#6FA58C'/></g>"
              "<g transform='translate(222 18)'><rect width='40' height='32' rx='12' fill='#fff'/>"
              "<path d='M13,10 L13,18 L18,18 L22,26 Q26,26 25,20 L31,20 Q33,19 32,16 L30,10Z' fill='#EE7A64'/></g>")
    return wrap(loop + thumbs + robot(140, 120, .6, GOLD_LT, GOLD)
                + person(64, 190, .82, SKIN[2], HAIR[3], NAVY, "short", "right")
                + person(216, 190, .82, SKIN[0], HAIR[2], CORAL, "bun", "left"))


def scene_template():
    """5. Picks become the Seattle Unlocked graphic."""
    card = ("<rect x='78' y='14' width='124' height='162' rx='14' fill='" + NAVY + "'/>"
            "<rect x='88' y='24' width='104' height='72' rx='10' fill='" + SKY + "'/>"
            + mountain(140, 96, 96, 44) + needle(118, 96, .55, NAVY)
            + "<text x='140' y='116' text-anchor='middle' font-family='Fredoka,Figtree,sans-serif' font-size='13' "
              "font-weight='600' fill='#fff'>This week, free</text>"
            + "".join(f"<rect x='92' y='{y}' width='{w}' height='7' rx='3.5' fill='#fff' opacity='.75'/>"
                      for y, w in [(126, 88), (138, 70), (150, 80)])
            + "<rect x='150' y='158' width='42' height='12' rx='6' fill='" + GOLD + "'/>")
    sp = sparkle(56, 40, .9, PLUM) + sparkle(226, 150, .9) + sparkle(228, 46, .6, SAGE)
    return wrap(card + sp)


def scene_post():
    """6. Posted on Instagram."""
    phone = ("<rect x='96' y='8' width='92' height='176' rx='18' fill='#2A2433'/>"
             "<rect x='102' y='20' width='80' height='152' rx='12' fill='#fff'/>"
             "<circle cx='114' cy='32' r='6' fill='" + PLUM + "'/><rect x='124' y='29' width='40' height='6' rx='3' "
             "fill='#E6DCD3'/>"
             "<rect x='102' y='44' width='80' height='80' fill='" + NAVY + "'/>"
             "<rect x='110' y='52' width='64' height='36' rx='6' fill='" + SKY + "'/>"
             + needle(128, 88, .32, NAVY)
             + "<rect x='112' y='96' width='56' height='6' rx='3' fill='#fff' opacity='.8'/>"
             + heart(114, 134, .8) + "<rect x='128' y='132' width='30' height='6' rx='3' fill='#E6DCD3'/>")
    pops = (heart(62, 60, 1.3) + heart(220, 46, 1.0, PLUM) + heart(232, 120, 1.4)
            + "<g transform='translate(30 118)'><rect width='50' height='26' rx='13' fill='#fff'/>"
              + heart(16, 10, .7) + "<text x='36' y='17' text-anchor='middle' font-family='Figtree,sans-serif' "
              "font-size='11' font-weight='700' fill='#3A2833'>2.4k</text></g>")
    return wrap(phone + pops)


def scene_community():
    """7. People show up, and Seattle gets a little closer."""
    bg = (mountain(70, 150, 150, 70) + needle(238, 150, .95, "#9FB3CF")
          + "<rect x='0' y='146' width='280' height='44' fill='#F7E4CF'/>")
    ppl = (person(46, 190, .66, SKIN[3], HAIR[3], GOLD, "short", "up")
           + person(108, 190, .74, SKIN[0], HAIR[0], PLUM, "long", "up")
           + person(172, 190, .74, SKIN[1], HAIR[1], SAGE, "short", "up")
           + person(234, 190, .66, SKIN[2], HAIR[2], CORAL, "bun", "up"))
    confetti = (sparkle(30, 30, .7, PLUM) + sparkle(140, 22, .9) + sparkle(250, 28, .6, SAGE)
                + heart(196, 36, .7, CORAL))
    return wrap("<rect width='280' height='190' rx='22' fill='" + SKY + "'/>" + bg + confetti + ppl)


SCENES = [scene_pull, scene_parse, scene_match, scene_loop, scene_template, scene_post, scene_community]
