import { useEffect, useState } from 'react'
import { EditorContent, useEditor, useEditorState } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import type { ServiceDocument } from '../../types'

const safeUrl = (url: string) => /^(https?:\/\/[^\s/]+|mailto:[^\s@]+@[^\s@]+)[^\s]*$/i.test(url)

export function RichTextEditor({ initialValue, onChange, readOnly = false, disabled = false, error }: { initialValue?: ServiceDocument | null; onChange?: (value: ServiceDocument) => void; readOnly?: boolean; disabled?: boolean; error?: string }) {
  const [linkOpen, setLinkOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [linkError, setLinkError] = useState('')
  const editor = useEditor({
    extensions: [StarterKit.configure({ heading: { levels: [1, 2, 3] }, code: false, codeBlock: false, strike: false, underline: false, horizontalRule: false, link: { openOnClick: readOnly, autolink: false, isAllowedUri: safeUrl, HTMLAttributes: { target: '_blank', rel: 'noopener noreferrer' } } })],
    content: initialValue?.doc ?? { type: 'doc', content: [{ type: 'paragraph' }] },
    editable: !readOnly && !disabled,
    editorProps: { attributes: { class: 'rich-text-content', role: 'textbox', 'aria-label': 'Descrição formatada', 'aria-multiline': 'true', 'aria-describedby': 'service-description-hint' } },
    onUpdate: ({ editor: current }) => onChange?.({ version: 1, doc: current.getJSON() as ServiceDocument['doc'] }),
  })
  useEffect(() => { editor?.setEditable(!readOnly && !disabled) }, [editor, readOnly, disabled])
  useEffect(() => { editor?.view.dom.setAttribute('aria-invalid', String(Boolean(error))) }, [editor, error])
  const state = useEditorState({ editor, selector: ({ editor: current }) => current ? { bold: current.isActive('bold'), italic: current.isActive('italic'), bullet: current.isActive('bulletList'), ordered: current.isActive('orderedList'), quote: current.isActive('blockquote'), heading: current.getAttributes('heading').level ?? 0, count: current.getText().length, undo: current.can().undo(), redo: current.can().redo() } : null })
  if (!editor || !state) return null
  const tool = (label: string, action: () => void, active = false, unavailable = false) => <button type="button" aria-label={label} aria-pressed={active} disabled={disabled || unavailable} onClick={action}>{label}</button>
  return <div className={`rich-editor ${readOnly ? 'rich-editor--readonly' : ''}`}>
    {!readOnly && <div className="rich-editor__toolbar" role="toolbar" aria-label="Formatação da descrição">
      <select aria-label="Estilo do texto" disabled={disabled} value={state.heading} onChange={(event) => { const level = Number(event.target.value); if (level) editor.chain().focus().setHeading({ level: level as 1 | 2 | 3 }).run(); else editor.chain().focus().setParagraph().run() }}><option value={0}>Texto</option><option value={1}>Título 1</option><option value={2}>Título 2</option><option value={3}>Título 3</option></select>
      {tool('Negrito', () => editor.chain().focus().toggleBold().run(), state.bold)}
      {tool('Itálico', () => editor.chain().focus().toggleItalic().run(), state.italic)}
      {tool('Lista', () => editor.chain().focus().toggleBulletList().run(), state.bullet)}
      {tool('Lista numerada', () => editor.chain().focus().toggleOrderedList().run(), state.ordered)}
      {tool('Citação', () => editor.chain().focus().toggleBlockquote().run(), state.quote)}
      {tool('Link', () => { setUrl(editor.getAttributes('link').href ?? ''); setLinkError(''); setLinkOpen(!linkOpen) })}
      {tool('Desfazer', () => editor.chain().focus().undo().run(), false, !state.undo)}
      {tool('Refazer', () => editor.chain().focus().redo().run(), false, !state.redo)}
      {tool('Inserir modelo', () => editor.chain().focus().insertContent(['Sobre o serviço', 'Benefícios', 'O que está incluído', 'Como funciona'].flatMap((text) => [{ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text }] }, { type: 'paragraph' }])).run())}
    </div>}
    {!readOnly && linkOpen && <div className="rich-editor__link"><label htmlFor="description-link">Endereço do link</label><input id="description-link" value={url} disabled={disabled} onChange={(event) => setUrl(event.target.value)} placeholder="https://... ou mailto:..." aria-invalid={Boolean(linkError)} /><button type="button" disabled={disabled} onClick={() => { if (!safeUrl(url)) { setLinkError('Informe um link https://, http:// ou mailto: válido.'); return } editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run(); setLinkOpen(false) }}>Aplicar link</button><button type="button" disabled={disabled} onClick={() => { editor.chain().focus().extendMarkRange('link').unsetLink().run(); setLinkOpen(false) }}>Remover link</button>{linkError && <p role="alert">{linkError}</p>}</div>}
    <EditorContent editor={editor} />
    {!readOnly && <p id="service-description-hint" className={error ? 'text-red-700' : 'text-slate-500'}>{error || `Use os botões ou atalhos como #, ## e **texto**. ${state.count.toLocaleString('pt-BR')}/20.000 caracteres.`}</p>}
  </div>
}
