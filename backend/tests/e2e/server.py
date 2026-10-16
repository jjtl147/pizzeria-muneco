"""Flask real + PostgreSQL aislado. Credenciales ficticias, sin servicios externos."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import os
import re
import uuid
import time
import httpx
from types import SimpleNamespace
from postgrest.exceptions import APIError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
import auth_supabase
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
    def ilike(self, campo, valor):
        self.params.append(valor); self.filtros.append(f't.{identificador(campo)} ILIKE ${len(self.params)}'); return self
    def gte(self, campo, valor):
        self.params.append(valor); self.filtros.append(f't.{identificador(campo)} >= ${len(self.params)}'); return self
    def lt(self, campo, valor):
        self.params.append(valor); self.filtros.append(f't.{identificador(campo)} < ${len(self.params)}'); return self
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


# Auth simulado exclusivamente en este ejecutable de pruebas. Ninguna ruta de
# producción tiene un bypass y no se envían correos ni peticiones externas.
sesiones = {}
refresh_revocados = set()
recuperaciones = {}


def nueva_sesion(user_id):
    token = uuid.uuid4().hex
    refresh = uuid.uuid4().hex
    datos = {'access_token': token, 'refresh_token': refresh, 'expires_in': 3600,
             'user': {'id': user_id}}
    sesiones[token] = datos
    return datos


def auth_falso(method, path, datos=None, token=None):
    ruta = path.split('?')[0]
    if ruta == '/user':
        if token not in sesiones: raise auth_supabase.AuthFailure(401)
        identidad = sesiones[token]['user']
        if method == 'PUT':
            sql('UPDATE auth.users SET encrypted_password=$1 WHERE id=$2',
                [generate_password_hash(datos['password']), identidad['id']])
        return identidad
    if ruta == '/token':
        if 'grant_type=refresh_token' in path:
            anterior = next((s for s in sesiones.values() if s['refresh_token'] == datos['refresh_token']), None)
            if not anterior or datos['refresh_token'] in refresh_revocados:
                raise auth_supabase.AuthFailure(400, 'invalid_credentials')
            refresh_revocados.add(anterior['refresh_token'])
            return nueva_sesion(anterior['user']['id'])
        users = sql('SELECT id,encrypted_password FROM auth.users WHERE email=$1', [datos['email']])
        if not users or not check_password_hash(users[0]['encrypted_password'], datos['password']):
            raise auth_supabase.AuthFailure(400, 'invalid_credentials')
        return nueva_sesion(users[0]['id'])
    if ruta in ('/signup', '/admin/users'):
        user_id = str(uuid.uuid4())
        sql('INSERT INTO auth.users(id,email,encrypted_password,raw_app_meta_data,raw_user_meta_data) VALUES($1,$2,$3,$4::jsonb,$5::jsonb)',
            [user_id, datos['email'], generate_password_hash(datos['password']),
             json.dumps(datos.get('app_metadata', {})), json.dumps(datos.get('data', datos.get('user_metadata', {})))])
        return nueva_sesion(user_id) if ruta == '/signup' else {'id': user_id}
    if ruta == '/recover':
        users = sql('SELECT id FROM auth.users WHERE email=$1', [datos['email']])
        if users:
            sesion = nueva_sesion(users[0]['id'])
            recuperaciones[datos['email']] = '/restablecer#access_token=' + sesion['access_token'] + '&refresh_token=' + sesion['refresh_token'] + '&type=recovery&expires_in=3600'
        return {}
    if ruta == '/logout':
        anterior = sesiones.get(token)
        if anterior and 'scope=global' in path:
            for sesion in sesiones.values():
                if sesion['user'] == anterior['user']: refresh_revocados.add(sesion['refresh_token'])
        elif anterior:
            refresh_revocados.add(anterior['refresh_token'])
        return {}
    raise RuntimeError('Ruta de Auth no simulada')


@backend.app.get('/__test/enlace/<email>')
def enlace_prueba(email):
    return jsonify({'url': recuperaciones[email]})


if __name__=='__main__':
    backend.get_supabase_client=lambda: DB()
    backend.solicitar=auth_falso
    auth_supabase.solicitar=auth_falso
    os.environ['TELEGRAM_ENABLED']='0'; os.environ['ASSISTANT_ENABLED']='0'
    password=generate_password_hash('Prueba123!')
    for email,roles in [('cliente@example.test',['CLIENTE']),('vendedor@example.test',['VENDEDOR']),('admin@example.test',['CLIENTE','ADMINISTRADOR'])]:
        sql('INSERT INTO usuarios(nombre,email,password_hash,roles) VALUES($1,$2,$3,$4::text[])',[email.split('@')[0],email,password,roles])
    sql("INSERT INTO categorias(nombre) VALUES('Pizzas')")
    for tamano,precio in [('Mediana',12),('Familiar',20)]:
        DB().rpc('crear_producto_con_inventario',{'p_producto':{'nombre':'Pizza prueba','tamano':tamano,'precio':precio,'categoria_id':1,'imagen':'https://placehold.co/400x300?text=Pizza'},'p_stock_inicial':10}).execute()
    backend.app.run(host='127.0.0.1',port=5059,debug=False)
