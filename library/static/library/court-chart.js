(function (global) {
    "use strict";

    var SVG_NS = "http://www.w3.org/2000/svg";
    var XLINK_NS = "http://www.w3.org/1999/xlink";

    function courtSvgMarkup(id) {
        return ""
            + "<svg viewBox=\"0 0 500 470\" xmlns=\"" + SVG_NS + "\" xmlns:xlink=\"" + XLINK_NS + "\" aria-label=\"Shot chart\">"
            + "<defs><radialGradient id=\"" + id + "-paintGrad\" cx=\"50%\" cy=\"88%\" r=\"60%\">"
            + "<stop offset=\"0%\" stop-color=\"#1f262e\"/><stop offset=\"100%\" stop-color=\"transparent\"/>"
            + "</radialGradient></defs>"
            + "<rect x=\"0\" y=\"0\" width=\"500\" height=\"470\" fill=\"none\" stroke=\"#37404B\" stroke-width=\"2\" rx=\"4\"/>"
            + "<rect x=\"170\" y=\"280\" width=\"160\" height=\"190\" fill=\"url(#" + id + "-paintGrad)\" stroke=\"#5A6472\" stroke-width=\"1.4\"/>"
            + "<circle cx=\"250\" cy=\"417\" r=\"7.5\" fill=\"none\" stroke=\"#F0702F\" stroke-width=\"2\"/>"
            + "<line x1=\"220\" y1=\"431\" x2=\"280\" y2=\"431\" stroke=\"#5A6472\" stroke-width=\"2.5\"/>"
            + "<circle cx=\"250\" cy=\"280\" r=\"60\" fill=\"none\" stroke=\"#5A6472\" stroke-width=\"1.4\"/>"
            + "<path d=\"M 210 417 A 40 40 0 0 0 290 417\" fill=\"none\" stroke=\"#5A6472\" stroke-width=\"1.2\"/>"
            + "<line x1=\"30\" y1=\"470\" x2=\"30\" y2=\"327\" stroke=\"#5A6472\" stroke-width=\"1.6\"/>"
            + "<line x1=\"470\" y1=\"470\" x2=\"470\" y2=\"327\" stroke=\"#5A6472\" stroke-width=\"1.6\"/>"
            + "<path d=\"M 30 327 A 237.5 237.5 0 0 1 470 327\" fill=\"none\" stroke=\"#5A6472\" stroke-width=\"1.6\"/>"
            + "<g class=\"dots-layer\"></g>"
            + "</svg>";
    }

    function buildClipUrl(s) {
        if (!(s.gid && s.eid != null && s.season)) return null;
        return "https://www.nba.com/stats/events/?GameEventID=" + s.eid
            + "&GameID=" + s.gid + "&Season=" + s.season + "&flag=1&sct=plot";
    }

    function render(container, shots, opts) {
        opts = opts || {};
        var id = opts.id || ("chart-" + Math.random().toString(36).slice(2));

        container.innerHTML = courtSvgMarkup(id);
        var svg = container.querySelector("svg");
        var dotsLayer = svg.querySelector(".dots-layer");

        function setShots(nextShots) {
            while (dotsLayer.firstChild) dotsLayer.removeChild(dotsLayer.firstChild);

            (nextShots || []).forEach(function (s) {
                var cx = 250 + s.x;
                var cy = 417 - s.y;
                if (cx < 2 || cx > 498 || cy < 2 || cy > 468) return;

                var c = document.createElementNS(SVG_NS, "circle");
                c.setAttribute("cx", cx);
                c.setAttribute("cy", cy);
                if (s.made) {
                    c.setAttribute("r", 3.4);
                    c.setAttribute("fill", opts.makeColor || "#F0702F");
                    c.setAttribute("fill-opacity", "0.9");
                } else {
                    c.setAttribute("r", 3);
                    c.setAttribute("fill", "none");
                    c.setAttribute("stroke", opts.missColor || "#6B7685");
                    c.setAttribute("stroke-width", "1.2");
                    c.setAttribute("stroke-opacity", "0.7");
                }

                var clipUrl = buildClipUrl(s);
                if (clipUrl) {
                    var a = document.createElementNS(SVG_NS, "a");
                    a.setAttributeNS(XLINK_NS, "href", clipUrl);
                    a.setAttribute("href", clipUrl);
                    a.setAttribute("target", "_blank");
                    a.setAttribute("rel", "noopener");
                    a.style.cursor = "pointer";

                    var hit = document.createElementNS(SVG_NS, "circle");
                    hit.setAttribute("cx", cx);
                    hit.setAttribute("cy", cy);
                    hit.setAttribute("r", 8);
                    hit.setAttribute("fill", "transparent");

                    a.appendChild(hit);
                    a.appendChild(c);
                    dotsLayer.appendChild(a);
                } else {
                    dotsLayer.appendChild(c);
                }
            });
        }

        setShots(shots);
        return { svg: svg, dotsLayer: dotsLayer, setShots: setShots };
    }

    var HOOP_X = 250;
    var HOOP_Y = 417;
    var FAR = 1000;
    var CORNER_ANGLE = 67.750976; // must match _CORNER_ANGLE in zone_wedges.py

    var AREA_KEYS = ["Left Side(L)", "Left Side Center(LC)", "Center(C)", "Right Side Center(RC)", "Right Side(R)"];
    var THREE_ARC = "M30,470 L30,327 A237.5,237.5 0 0 1 470,327 L470,470 Z";
    var PAINT_RECT = "M170,280 L330,280 L330,470 L170,470 Z";
    var ATB_REGION = "M0,0 H500 V470 H0 Z " + THREE_ARC;
    var MR_REGION = THREE_ARC + " " + PAINT_RECT;

    function rayPoint(angle, len) {
        var r = angle * Math.PI / 180;
        return [HOOP_X + len * Math.sin(r), HOOP_Y - len * Math.cos(r)];
    }

    function fmtPoint(p) {
        return p[0].toFixed(1) + "," + p[1].toFixed(1);
    }

    // Wedge polygon from the hoop. lo === null extends the wedge to the far
    // left (and behind the hoop); hi === null does the same to the far right.
    function wedgePoints(lo, hi) {
        var hoop = [HOOP_X, HOOP_Y];
        var pts;
        if (lo === null) {
            pts = [hoop, rayPoint(hi, FAR), [-4750, HOOP_Y], [-4750, 5000], [HOOP_X, 5000]];
        } else if (hi === null) {
            pts = [hoop, rayPoint(lo, FAR), [5250, HOOP_Y], [5250, 5000], [HOOP_X, 5000]];
        } else {
            pts = [hoop, rayPoint(lo, FAR), rayPoint(hi, FAR)];
        }
        return pts.map(fmtPoint).join(" ");
    }

    // Interior wedge boundaries (degrees from straight up, negative = left),
    // matching classify_zone_area in zone_wedges.py.
    var SPLIT_ZONES = {
        "Above the Break 3": {
            region: ATB_REGION, clip: "atb",
            bounds: [-CORNER_ANGLE, -18, 18, CORNER_ANGLE],
            labels: [[45, 225], [118, 160], [250, 110], [382, 160], [455, 225]],
            small: [true, false, false, false, true]
        },
        "Mid-Range": {
            region: MR_REGION, clip: "mr",
            bounds: [-54, -18, 18, 54],
            labels: [[100, 385], [128, 250], [250, 228], [372, 250], [400, 385]],
            small: [false, false, false, false, false]
        }
    };

    var ZONE_ORDER = [];
    var ZONE_SHAPES = {};

    function addZone(key, shape) {
        ZONE_ORDER.push(key);
        ZONE_SHAPES[key] = shape;
    }

    ["Above the Break 3", "Mid-Range"].forEach(function (basic) {
        var cfg = SPLIT_ZONES[basic];
        AREA_KEYS.forEach(function (area, i) {
            var lo = (i === 0) ? null : cfg.bounds[i - 1];
            var hi = (i === 4) ? null : cfg.bounds[i];
            addZone(basic + "|" + area, {
                path: cfg.region, fillRule: "evenodd",
                wedge: wedgePoints(lo, hi),
                label: cfg.labels[i], small: cfg.small[i]
            });
        });
    });

    addZone("In The Paint (Non-RA)", {
        path: PAINT_RECT + " M210,417 A40,40 0 0 1 290,417 Z",
        fillRule: "evenodd", label: [250, 330]
    });
    addZone("Restricted Area", {
        path: "M210,417 A40,40 0 0 1 290,417 Z",
        fillRule: "nonzero", label: [250, 398]
    });
    addZone("Left Corner 3", {
        path: "M0,327 L30,327 L30,470 L0,470 Z",
        fillRule: "nonzero", label: [15, 400], rotate: true
    });
    addZone("Right Corner 3", {
        path: "M470,327 L500,327 L500,470 L470,470 Z",
        fillRule: "nonzero", label: [485, 400], rotate: true
    });

    function zoneColor(pct) {
        var t = Math.max(0, Math.min(1, pct / 65));
        var cold = [58, 90, 120];
        var hot = [240, 112, 47];
        var r = Math.round(cold[0] + (hot[0] - cold[0]) * t);
        var g = Math.round(cold[1] + (hot[1] - cold[1]) * t);
        var b = Math.round(cold[2] + (hot[2] - cold[2]) * t);
        return "rgb(" + r + "," + g + "," + b + ")";
    }

    function zoneDiffColor(diff) {
        var t = Math.max(-1, Math.min(1, diff / 12));
        var neutral = [70, 78, 88];
        var cold = [58, 90, 120];
        var hot = [240, 112, 47];
        var target = t < 0 ? cold : hot;
        var frac = Math.abs(t);
        var r = Math.round(neutral[0] + (target[0] - neutral[0]) * frac);
        var g = Math.round(neutral[1] + (target[1] - neutral[1]) * frac);
        var b = Math.round(neutral[2] + (target[2] - neutral[2]) * frac);
        return "rgb(" + r + "," + g + "," + b + ")";
    }

    function renderZones(container, zoneStats, opts) {
        opts = opts || {};
        var id = opts.id || ("zones-" + Math.random().toString(36).slice(2));

        var byZone = {};
        (zoneStats || []).forEach(function (z) { byZone[z.zone] = z; });

        var relativeMode = (zoneStats || []).some(function (z) {
            return z.diff !== null && z.diff !== undefined;
        });

        var defs = "<defs>"
            + "<clipPath id='" + id + "-mr'><path d='" + MR_REGION + "' clip-rule='evenodd'/></clipPath>"
            + "<clipPath id='" + id + "-atb'><path d='" + ATB_REGION + "' clip-rule='evenodd'/></clipPath>";
        ZONE_ORDER.forEach(function (name, i) {
            var shape = ZONE_SHAPES[name];
            if (shape.wedge) {
                defs += "<clipPath id='" + id + "-w" + i + "'><polygon points='" + shape.wedge + "'/></clipPath>";
            }
        });
        defs += "</defs>";

        var shapesMarkup = ZONE_ORDER.map(function (name, i) {
            var shape = ZONE_SHAPES[name];
            var z = byZone[name];
            var fill, fillOpacity;
            if (!z) {
                fill = "#1B2027"; fillOpacity = "0.4";
            } else if (relativeMode) {
                if (z.diff !== null && z.diff !== undefined) {
                    fill = zoneDiffColor(z.diff); fillOpacity = "0.92";
                } else {
                    fill = "#3A4048"; fillOpacity = "0.55";
                }
            } else {
                fill = zoneColor(z.pct); fillOpacity = "0.92";
            }
            var clipAttr = shape.wedge ? " clip-path='url(#" + id + "-w" + i + ")'" : "";
            return "<path d='" + shape.path + "' fill='" + fill + "' fill-opacity='" + fillOpacity
                + "' fill-rule='" + shape.fillRule + "' stroke='#0B0D10' stroke-width='1.5'" + clipAttr + "></path>";
        }).join("");

        var raysMarkup = Object.keys(SPLIT_ZONES).map(function (basic) {
            var cfg = SPLIT_ZONES[basic];
            return cfg.bounds.map(function (angle) {
                var p = rayPoint(angle, FAR);
                return "<line x1='" + HOOP_X + "' y1='" + HOOP_Y + "' x2='" + p[0].toFixed(1) + "' y2='" + p[1].toFixed(1)
                    + "' stroke='#0B0D10' stroke-width='1.5' clip-path='url(#" + id + "-" + cfg.clip + ")'/>";
            }).join("");
        }).join("");

        var labelsMarkup = ZONE_ORDER.map(function (name) {
            var shape = ZONE_SHAPES[name];
            var z = byZone[name];
            if (!z) return "";
            var x = shape.label[0], y = shape.label[1];
            var transform = shape.rotate ? " transform='rotate(-90 " + x + " " + y + ")'" : "";
            var mainSize = shape.small ? 15 : 20;
            var subSize = shape.small ? 8 : 10;
            var subOffset = shape.small ? 12 : 16;

            var mainLabel, subLabel;
            if (relativeMode && z.diff !== null && z.diff !== undefined) {
                mainLabel = (z.diff > 0 ? "+" : "") + z.diff + "%";
                subLabel = z.pct + "% (lg " + z.league_pct + "%)";
            } else if (relativeMode) {
                mainLabel = z.pct + "%";
                subLabel = "n=" + z.attempts + " (low)";
            } else {
                mainLabel = z.pct + "%";
                subLabel = z.makes + "/" + z.attempts;
            }

            return "<g" + transform + " text-anchor='middle'>"
                + "<text x='" + x + "' y='" + y + "' font-family='IBM Plex Mono, monospace' font-size='" + mainSize + "' font-weight='700' fill='#ECEAE4'>" + mainLabel + "</text>"
                + "<text x='" + x + "' y='" + (y + subOffset) + "' font-family='IBM Plex Mono, monospace' font-size='" + subSize + "' fill='#A8AFB8'>" + subLabel + "</text>"
                + "</g>";
        }).join("");

        var markup = ""
            + "<svg viewBox='0 0 500 470' xmlns='" + SVG_NS + "' aria-label='Shooting zone heatmap'>"
            + defs
            + shapesMarkup
            + raysMarkup
            + "<rect x='170' y='280' width='160' height='190' fill='none' stroke='#5A6472' stroke-width='1' rx='2'/>"
            + "<circle cx='250' cy='417' r='7.5' fill='none' stroke='#0B0D10' stroke-width='2'/>"
            + "<line x1='220' y1='431' x2='280' y2='431' stroke='#0B0D10' stroke-width='2.5'/>"
            + "<circle cx='250' cy='280' r='60' fill='none' stroke='#5A6472' stroke-width='1'/>"
            + "<rect x='0' y='0' width='500' height='470' fill='none' stroke='#37404B' stroke-width='2' rx='4'/>"
            + labelsMarkup
            + "</svg>";

        container.innerHTML = markup;
        return { svg: container.querySelector("svg"), relativeMode: relativeMode };
    }

    global.CourtChart = { render: render, renderZones: renderZones };
})(window);
