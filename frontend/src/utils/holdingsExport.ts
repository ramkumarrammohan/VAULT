import type { ConsolidatedHolding } from '@/types'

export interface HoldingsExportSection {
  label: string
  currency: string
  holdings: ConsolidatedHolding[]
}

export interface HoldingsExportFilters {
  account?: string
  stock?: string
}

const HEADERS = [
  'Currency',
  'Stock Symbol',
  'Stock Name',
  'Account',
  'Quantity',
  'Average Price',
  'Current Price',
  'Invested Value',
  'Current Value',
  'Gain/Loss',
  'Gain/Loss %'
] as const

const CONSOLIDATED_LABEL = 'Consolidated'

type CellValue = string | number | null

const round = (value: number): number => Math.round(value * 100) / 100

/**
 * Flattens the dashboard sections into export rows. When a stock is expanded in
 * the UI (present in `expandedStocks`), its per-account sub-holdings are included
 * directly below the consolidated row so the export matches what is on screen.
 */
const buildRows = (
  sections: HoldingsExportSection[],
  expandedStocks?: Set<number>
): CellValue[][] => {
  const rows: CellValue[][] = []

  for (const section of sections) {
    for (const holding of section.holdings) {
      const currency = holding.currency ?? section.currency

      rows.push([
        currency,
        holding.stock_symbol,
        holding.stock_name,
        CONSOLIDATED_LABEL,
        holding.quantity,
        round(holding.average_price),
        holding.current_price != null ? round(holding.current_price) : null,
        round(holding.invested_value),
        round(holding.current_value),
        round(holding.gain_loss),
        round(holding.gain_loss_percentage)
      ])

      if (expandedStocks?.has(holding.stock_id)) {
        for (const sub of holding.sub_holdings) {
          rows.push([
            sub.currency ?? currency,
            sub.stock_symbol,
            sub.stock_name,
            sub.account_name,
            sub.quantity,
            round(sub.average_price),
            sub.current_price != null ? round(sub.current_price) : null,
            round(sub.invested_value),
            round(sub.current_value),
            round(sub.gain_loss),
            round(sub.gain_loss_percentage)
          ])
        }
      }
    }
  }

  return rows
}

const escapeCsv = (value: CellValue): string => {
  if (value === null || value === undefined) return ''
  const str = String(value)
  if (/[",\r\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

const escapeXml = (value: CellValue): string => {
  if (value === null || value === undefined) return ''
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

export const buildHoldingsCsv = (
  sections: HoldingsExportSection[],
  expandedStocks?: Set<number>
): string => {
  const lines = [HEADERS.join(',')]
  for (const row of buildRows(sections, expandedStocks)) {
    lines.push(row.map(escapeCsv).join(','))
  }
  return lines.join('\r\n')
}

/**
 * Builds SpreadsheetML (an XML spreadsheet format Excel, LibreOffice and
 * Google Sheets all understand) so no third-party dependency is required.
 */
export const buildHoldingsExcelXml = (
  sections: HoldingsExportSection[],
  expandedStocks?: Set<number>
): string => {
  const headerCells = HEADERS.map(
    (header) => `<Cell><Data ss:Type="String">${escapeXml(header)}</Data></Cell>`
  ).join('')

  const bodyRows = buildRows(sections, expandedStocks)
    .map((row) => {
      const cells = row
        .map((cell) => {
          if (cell === null || cell === undefined || cell === '') {
            return '<Cell/>'
          }
          if (typeof cell === 'number') {
            return `<Cell><Data ss:Type="Number">${cell}</Data></Cell>`
          }
          return `<Cell><Data ss:Type="String">${escapeXml(cell)}</Data></Cell>`
        })
        .join('')
      return `<Row>${cells}</Row>`
    })
    .join('\n   ')

  return `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Worksheet ss:Name="Holdings">
  <Table>
   <Row>${headerCells}</Row>
   ${bodyRows}
  </Table>
 </Worksheet>
</Workbook>`
}

const slugify = (value: string): string =>
  value
    .trim()
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

export const buildHoldingsFilename = (
  extension: string,
  filters: HoldingsExportFilters = {}
): string => {
  const parts = ['holdings']
  if (filters.account) parts.push(slugify(filters.account))
  if (filters.stock) parts.push(slugify(filters.stock))
  parts.push(new Date().toISOString().slice(0, 10))
  return `${parts.join('_')}.${extension}`
}

export const downloadFile = (content: string, filename: string, mimeType: string): void => {
  const blob = new Blob([content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  window.URL.revokeObjectURL(url)
}
