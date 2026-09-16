import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Dialog } from './Dialog'

describe('Dialog', () => {
  it('abre com título acessível, fecha por Esc e devolve o foco', () => {
    const onClose = vi.fn()
    const trigger = document.createElement('button')
    document.body.appendChild(trigger)
    trigger.focus()
    const view = render(<Dialog open title="Novo cliente" onClose={onClose}><input aria-label="Nome" /></Dialog>)
    expect(screen.getByRole('dialog', { name: 'Novo cliente' })).toHaveAttribute('open')
    fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }))
    expect(onClose).toHaveBeenCalledOnce()
    view.unmount()
    expect(trigger).toHaveFocus()
    trigger.remove()
  })

  it('bloqueia fechamento durante o envio', () => {
    const onClose = vi.fn()
    render(<Dialog open busy title="Salvando" onClose={onClose}>Conteúdo</Dialog>)
    fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }))
    fireEvent.click(screen.getByRole('button', { name: 'Fechar diálogo' }))
    expect(onClose).not.toHaveBeenCalled()
  })
})
