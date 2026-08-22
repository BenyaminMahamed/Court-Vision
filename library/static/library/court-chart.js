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

    global.CourtChart = { render: render };
})(window);
