const CURRENCY_CONFIG: Record<string, { locale: string; currency: string }> = {
  INR: { locale: 'en-IN', currency: 'INR' },
  USD: { locale: 'en-US', currency: 'USD' },
}

const DEFAULT_CONFIG = { locale: 'en-US', currency: 'USD' }

export function formatCurrency(value: number, currency: string = 'INR'): string {
  const config = CURRENCY_CONFIG[currency.toUpperCase()] ?? DEFAULT_CONFIG
  return new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.currency,
    minimumFractionDigits: 2,
  }).format(value)
}
