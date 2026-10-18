
import { useEffect, useState } from 'react'
import './Chatbot.css'

// NUEVO (Jonathan, 2026-10-18): Django rechaza (403) cualquier POST sin token CSRF.
// GET /api/csrf/ deja la cookie 'csrftoken' y aquí se lee para mandarla en el encabezado X-CSRFToken.
function leerCookie(nombre: string): string {
  const fila = document.cookie.split('; ').find((c) => c.startsWith(`${nombre}=`))
  return fila ? decodeURIComponent(fila.split('=')[1]) : ''
}

// NUEVO (Jonathan, 2026-10-18): el bot responde con Markdown sencillo (listas y **negritas**).
// Antes se mostraba todo en un solo párrafo con los asteriscos visibles. Se arma con elementos de React,
// sin innerHTML, así que un texto del bot no puede inyectar HTML.
function conNegritas(linea: string) {
  return linea.split(/\*\*(.+?)\*\*/g).map((parte, i) => (i % 2 === 1 ? <strong key={i}>{parte}</strong> : parte))
}

function TextoBot({ texto }: { texto: string }) {
  return (
    <div className="chatbot-text">
      {texto.split('\n').filter((linea) => linea.trim() !== '').map((linea, i) => {
        const vineta = linea.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)$/)
        return vineta
          ? <p key={i} className="chatbot-bullet">• {conNegritas(vineta[1])}</p>
          : <p key={i}>{conNegritas(linea.replace(/^#+\s*/, ''))}</p>
      })}
    </div>
  )
}

// NUEVO (Jonathan, 2026-10-18): la conversación se guarda en el navegador para no perderla al recargar.
const CLAVE_SESION = 'agrocebada_chat_sesion'

function leerSesionGuardada(): number | null {
  try {
    const valor = Number(localStorage.getItem(CLAVE_SESION))
    return valor > 0 ? valor : null
  } catch {
    return null
  }
}

type Mensaje = {
  texto: string
  autor: 'usuario' | 'bot'
}

export default function Chatbot() {
  const [abierto, setAbierto] = useState(false)
  const [texto, setTexto] = useState('')
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    {
      // MODIFICADO (Jonathan, 2026-10-18): el asistente se llama Cebas.
      texto: '¡Hola! Soy Cebas, asistente de SocieData para el proyecto AgroCebada. Te ayudo a encontrar y entender la información de las parcelas. ¿Qué quieres saber?',
      autor: 'bot',
    },
  ])
  const [cargando, setCargando] = useState(false)
  // NUEVO (Jonathan, 2026-10-18): id de la conversación que devuelve Django; se manda en cada mensaje
  // para que el bot recuerde lo que se habló.
  const [sesionId, setSesionId] = useState<number | null>(leerSesionGuardada)

  useEffect(() => {
    fetch('/api/csrf/', { credentials: 'same-origin' }).catch(() => {})
  }, [])

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
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': leerCookie('csrftoken') },
        body: JSON.stringify({ texto: pregunta, idioma: 'es', sesion_id: sesionId }),
      })

      if (!respuesta.ok) {
        throw new Error(`Error HTTP ${respuesta.status}`)
      }

      const datos: { respuesta: string; sesion_id: number } = await respuesta.json()
      setSesionId(datos.sesion_id)
      try {
        localStorage.setItem(CLAVE_SESION, String(datos.sesion_id))
      } catch {
        // Sin localStorage (modo privado) la conversación solo dura mientras la página esté abierta.
      }

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
              <strong>Cebas</strong>
              <span>Asistente de SocieData · AgroCebada</span>
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
                {mensaje.autor === 'bot' ? <TextoBot texto={mensaje.texto} /> : <p>{mensaje.texto}</p>}
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
            <img src="/LogoBoton.svg" alt="Abrir chat con Cebas" />
        )}
        </button>
    </div>
  )
}
