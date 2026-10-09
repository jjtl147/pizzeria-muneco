import { Button } from 'react-bootstrap'
export default function Paginacion({ pagina, cambiar, hay_mas, cargando }) {
  return <div className="d-flex gap-3 align-items-center my-3">
    <Button variant="outline-secondary" disabled={pagina === 1 || cargando} onClick={() => cambiar(pagina - 1)}>Anterior</Button>
    <span>Página {pagina}</span><Button variant="outline-secondary" disabled={!hay_mas || cargando} onClick={() => cambiar(pagina + 1)}>Siguiente</Button>
  </div>
}
