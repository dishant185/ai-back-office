/**
 * Novera Audit Chart & Data Visualization Theme.
 *
 * Distinctive verified ledger styling:
 * - Novera Green (#176B50) & AI Brass (#A8792E) primary tones
 * - Hairline grid rules
 * - Tabular monospace axis ticks and values
 * - 2px sharp bordered ledger tooltips
 */

export const CHART_PALETTE: readonly string[] = [
  '#176B50', // 1: Novera Green (primary verified metric)
  '#A8792E', // 2: AI Brass (secondary / projection metric)
  '#2D8A68', // 3: Bright Forest Green
  '#416B7A', // 4: Audit Slate Blue
  '#7D6B58', // 5: Earth Ochre
  '#B33A3A', // 6: Flag Red (variance / risk)
  '#172125', // 7: Deep Ink
  '#66716C', // 8: Muted Ledger
] as const

export function getChartColor(index: number): string {
  return CHART_PALETTE[index % CHART_PALETTE.length]
}

export const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: '#11181B',
    border: '1px solid #334045',
    borderRadius: '2px',
    color: '#F3F5F1',
    fontSize: '11px',
    fontFamily: 'IBM Plex Mono, monospace',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
    padding: '8px 12px',
  },
  itemStyle: {
    color: '#E8ECE6',
    fontSize: '11px',
    fontFamily: 'IBM Plex Mono, monospace',
    padding: '2px 0',
  },
  labelStyle: {
    color: '#9EABA4',
    fontWeight: 500,
    fontSize: '10px',
    fontFamily: 'Inter, sans-serif',
    marginBottom: '4px',
    borderBottom: '1px solid #233036',
    paddingBottom: '2px',
  },
}

export const CHART_GRID_STYLE = {
  strokeDasharray: '2 2',
  stroke: 'var(--color-novera-rule, #C7CEC8)',
  opacity: 0.5,
}

export const CHART_AXIS_STYLE = {
  tick: {
    fontSize: 10,
    fontFamily: 'IBM Plex Mono, monospace',
    fill: 'var(--color-novera-muted, #66716C)',
  },
  axisLine: {
    stroke: 'var(--color-novera-rule, #C7CEC8)',
  },
}
