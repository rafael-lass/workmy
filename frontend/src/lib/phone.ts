const onlyDigits = (value: string) => value.replace(/\D/g, '')

export function maskBrazilianPhone(value: string): string {
  const digits = onlyDigits(value).replace(/^55(?=\d{10,11}$)/, '').slice(0, 11)
  if (!digits) return ''
  if (digits.length <= 2) return `(${digits}`
  const ddd = digits.slice(0, 2)
  const number = digits.slice(2)
  if (number.length <= 4) return `(${ddd}) ${number}`
  if (number.length <= 8) return `(${ddd}) ${number.slice(0, 4)}-${number.slice(4)}`
  return `(${ddd}) ${number.slice(0, 5)}-${number.slice(5)}`
}

export function isMaskedBrazilianPhoneValid(value: string): boolean {
  if (!value.trim()) return true
  const digits = onlyDigits(value)
  if (digits.length === 10) return !digits.startsWith('0') && !['0', '1'].includes(digits[2])
  return digits.length === 11 && !digits.startsWith('0') && digits[2] === '9'
}
