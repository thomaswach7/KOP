// Erzeugt die Daten für die SVG-Vorschau aus dem Analyse-Ergebnis (reine Funktion, testbar ohne DOM).
// Die Y-Achse wird gespiegelt, damit das Teil wie im CAD erscheint (DXF: Y nach oben, SVG: Y nach unten).

const fmt = (v) => {
  const s = v.toFixed(3).replace(/\.?0+$/, '');
  return s === '-0' ? '0' : s;
};

function contourPath(c) {
  const first = c.prims[0];
  let d = `M${fmt(first.x0)} ${fmt(-first.y0)}`;
  for (const p of c.prims) {
    if (p.k === 'L') {
      d += `L${fmt(p.x1)} ${fmt(-p.y1)}`;
      continue;
    }
    const r = fmt(p.r);
    const sweep = p.sw > 0 ? 0 : 1; // CCW in der Zeichnung = CCW auf dem Bildschirm
    if (Math.abs(p.sw) >= 2 * Math.PI - 1e-9) {
      // Vollkreis: SVG kennt keinen Bogen mit Start = Ende → zwei Halbbögen
      const mx = 2 * p.cx - p.x0;
      const my = 2 * p.cy - p.y0;
      d += `A${r} ${r} 0 0 ${sweep} ${fmt(mx)} ${fmt(-my)}A${r} ${r} 0 0 ${sweep} ${fmt(p.x1)} ${fmt(-p.y1)}`;
    } else {
      const large = Math.abs(p.sw) > Math.PI ? 1 : 0;
      d += `A${r} ${r} 0 ${large} ${sweep} ${fmt(p.x1)} ${fmt(-p.y1)}`;
    }
  }
  return c.closed ? `${d}Z` : d;
}

/**
 * @param {ReturnType<import('../geom/analyze.js').analyze>} analysis
 * @returns {{viewBox: number[], outer: string, inner: string, open: string, fill: string,
 *            gaps: number[][], markerRadius: number} | null}
 */
export function previewData(analysis) {
  if (!analysis.bbox) return null;
  let outer = '';
  let inner = '';
  let open = '';
  for (const c of analysis.contours) {
    const d = contourPath(c);
    if (c.role === 'outer') outer += d;
    else if (c.role === 'inner') inner += d;
    else open += d;
  }
  const { minX, maxY, w, h } = analysis.bbox;
  const span = Math.max(w, h) || 1;
  const pad = span * 0.05;
  return {
    viewBox: [minX - pad, -maxY - pad, w + 2 * pad, h + 2 * pad],
    outer, inner, open,
    fill: outer + inner,
    gaps: analysis.openEnds.map(([x, y]) => [x, -y]),
    markerRadius: span * 0.012,
  };
}
