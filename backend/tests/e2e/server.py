"""Flask real + PostgreSQL aislado. Credenciales ficticias, sin servicios externos."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import os
import re
import httpx
from types import SimpleNamespace
from postgrest.exceptions import APIError
from werkzeug.security import generate_password_hash
import app as backend


def sql(query, params=None):
    response = httpx.post('http://127.0.0.1:54329/sql', json={'sql': query, 'params': params or []}, timeout=15)
    if response.status_code != 200:
        error = response.json()
        raise APIError({**error, 'details': None, 'hint': None})
    return response.json()['rows']


def identificador(valor):
    if not re.fullmatch(r'[a-z_]+', valor): raise ValueError('Identificador de prueba inválido')
    return valor


class Consulta:
    def __init__(self, tabla):
        self.tabla = identificador(tabla); self.filtros = []; self.params = []
        self.seleccion = '*'; self.orden = ''; self.limite = ''; self.operacion = 'SELECT'; self.datos = None
    def select(self, campos): self.seleccion = campos; return self
    def eq(self, campo, valor):
        self.params.append(valor); self.filtros.append(f't.{identificador(campo)}=${len(self.params)}'); return self
    def in_(self, campo, valores):
        self.params.append(valores); self.filtros.append(f't.{identificador(campo)}=ANY(${len(self.params)}::integer[])'); return self
    def contains(self, campo, valores):
        self.params.append(valores); self.filtros.append(f't.{identificador(campo)} @> ${len(self.params)}::text[]'); return self
    def order(self, campo, desc=False): self.orden=f' ORDER BY t.{identificador(campo)} '+('DESC' if desc else 'ASC'); return self
    def limit(self, n): self.limite=f' LIMIT {int(n)}'; return self
    def range(self, inicio, fin): self.limite=f' LIMIT {fin-inicio+1} OFFSET {inicio}'; return self
    def insert(self, datos): self.operacion='INSERT'; self.datos=datos; return self
    def update(self, datos): self.operacion='UPDATE'; self.datos=datos; return self
    def execute(self):
        where=' WHERE '+' AND '.join(self.filtros) if self.filtros else ''
        if self.operacion in ('INSERT','UPDATE'):
            campos=[identificador(k) for k in self.datos]
            if self.operacion=='INSERT':
                params=list(self.datos.values()); indices=','.join(f'${i+1}' for i in range(len(params)))
                query=f"INSERT INTO {self.tabla} ({','.join(campos)}) VALUES ({indices}) RETURNING *"
            else:
                params=self.params+list(self.datos.values())
                asignaciones=','.join(f'{k}=${len(self.params)+i+1}' for i,k in enumerate(campos))
                query=f'UPDATE {self.tabla} t SET {asignaciones}{where} RETURNING *'
            return SimpleNamespace(data=sql(query,params))
        relaciones={
            'inventario': "(SELECT to_jsonb(i) FROM inventario i WHERE i.producto_id=t.id)",
            'productos': "(SELECT to_jsonb(p) FROM productos p WHERE p.id=t.producto_id)",
            'usuarios': "(SELECT to_jsonb(u)-'password_hash' FROM usuarios u WHERE u.id="+ ('t.vendedor_id' if self.tabla=='ventas' else 't.usuario_id')+")",
            'detalle_pedidos': "COALESCE((SELECT jsonb_agg(to_jsonb(d)) FROM detalle_pedidos d WHERE d.pedido_id=t.id),'[]'::jsonb)",
            'ventas': "(SELECT to_jsonb(v) FROM ventas v WHERE v.pedido_id=t.id)",
        }
        if '(' in self.seleccion:
            expresion='to_jsonb(t)'
            for nombre, subquery in relaciones.items():
                if nombre+'(' in self.seleccion: expresion+=f" || jsonb_build_object('{nombre}',{subquery})"
            query=f'SELECT {expresion} AS resultado FROM {self.tabla} t{where}{self.orden}{self.limite}'
            rows=[r['resultado'] for r in sql(query,self.params)]
        else:
            campos='t.*' if self.seleccion=='*' else ','.join('t.'+identificador(c.strip()) for c in self.seleccion.split(','))
            rows=sql(f'SELECT {campos} FROM {self.tabla} t{where}{self.orden}{self.limite}',self.params)
        return SimpleNamespace(data=rows)


class DB:
    def table(self, nombre): return Consulta(nombre)
    def rpc(self, nombre, argumentos):
        class RPC:
            def execute(self):
                params=[]; partes=[]
                for clave, valor in argumentos.items():
                    if isinstance(valor,(list,dict)) and clave!='p_roles':
                        params.append(json.dumps(valor)); conversion='::jsonb'
                    elif clave=='p_roles': params.append(valor); conversion='::text[]'
                    else: params.append(valor); conversion=''
                    partes.append(f'{identificador(clave)} => ${len(params)}{conversion}')
                rows=sql(f"SELECT {identificador(nombre)}({','.join(partes)}) AS resultado",params)
                return SimpleNamespace(data=rows[0]['resultado'])
        return RPC()


if __name__=='__main__':
    backend.get_supabase_client=lambda: DB()
    backend.JWT_SECRET_KEY='clave-exclusiva-para-las-pruebas-e2e-de-muneco'
    os.environ['TELEGRAM_ENABLED']='0'; os.environ['ASSISTANT_ENABLED']='0'
    password=generate_password_hash('Prueba123!')
    for email,roles in [('cliente@example.test',['CLIENTE']),('vendedor@example.test',['VENDEDOR']),('admin@example.test',['CLIENTE','ADMINISTRADOR'])]:
        sql('INSERT INTO usuarios(nombre,email,password_hash,roles) VALUES($1,$2,$3,$4::text[])',[email.split('@')[0],email,password,roles])
    sql("INSERT INTO categorias(nombre) VALUES('Pizzas')")
    for tamano,precio in [('Mediana',12),('Familiar',20)]:
        DB().rpc('crear_producto_con_inventario',{'p_producto':{'nombre':'Pizza prueba','tamano':tamano,'precio':precio,'categoria_id':1,'imagen':'https://placehold.co/400x300?text=Pizza'},'p_stock_inicial':10}).execute()
    backend.app.run(host='127.0.0.1',port=5059,debug=False)
