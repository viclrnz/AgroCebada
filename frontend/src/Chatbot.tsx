
import { useState } from 'react'
import './Chatbot.css'

type Mensaje = {
  texto: string
  autor: 'usuario' | 'bot'
}

export default function Chatbot() {
  const [abierto, setAbierto] = useState(false)
  const [texto, setTexto] = useState('')
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    {
      texto: '¡Hola! Soy el asistente de SocieData. ¿En qué puedo ayudarte?',
      autor: 'bot',
    },
  ])
  const [cargando, setCargando] = useState(false)

  async function enviarMensaje(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const pregunta = texto.trim()

    if (!pregunta || cargando) return

    setMensajes((anteriores) => [
      ...anteriores,
      { texto: pregunta, autor: 'usuario' },
    ])
    setTexto('')
    setCargando(true)

    try {
      const respuesta = await fetch('/api/chatbot/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: pregunta, idioma: 'es' }),
      })

      if (!respuesta.ok) {
        throw new Error(`Error HTTP ${respuesta.status}`)
      }

      const datos: { respuesta: string } = await respuesta.json()

      setMensajes((anteriores) => [
        ...anteriores,
        {
          texto: datos.respuesta,
          autor: 'bot',
        },
      ])
    } catch {
      setMensajes((anteriores) => [
        ...anteriores,
        {
          texto: 'No pude conectar con el asistente. Inténtalo de nuevo.',
          autor: 'bot',
        },
      ])
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="chatbot-widget">
      {abierto && (
        <section className="chatbot-panel">
          <header className="chatbot-header">
            <img src="/LogoBoton.svg" alt="SocieData" />
            <div className="chatbot-heading">
              <strong>SocieData Assistant</strong>
              <span>Asistente de AgroCebada</span>
            </div>
            <button
              className="chatbot-close"
              onClick={() => setAbierto(false)}
              aria-label="Cerrar chat"
            >
              ×
            </button>
          </header>

          <div className="chatbot-messages">
            {mensajes.map((mensaje, indice) => (
              <div
                key={indice}
                className={`chatbot-message ${mensaje.autor}`}
              >
                {mensaje.autor === 'bot' && (
                  <img src="/LogoChatbot.svg" alt="" />
                )}
                <p>{mensaje.texto}</p>
              </div>
            ))}

            {cargando && (
              <div className="chatbot-message bot">
                <img src="/LogoChatbot.svg" alt="" />
                <div className="chatbot-typing" aria-label="Escribiendo">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
          </div>

          <form className="chatbot-form" onSubmit={enviarMensaje}>
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Escribe tu pregunta..."
              aria-label="Escribe tu pregunta"
              disabled={cargando}
            />
            <button type="submit" disabled={cargando || !texto.trim()}>
              ➤
            </button>
          </form>
        </section>
      )}

        <button
        className="chatbot-toggle"
        onClick={() => setAbierto(!abierto)}
        aria-label={abierto ? 'Cerrar chat' : 'Abrir chat'}
        >
        {abierto ? (
            <span className="chatbot-toggle-close">×</span>
        ) : (
            <img src="/LogoBoton.svg" alt="Abrir chat de SocieData" />
        )}
        </button>
    </div>
  )
}
