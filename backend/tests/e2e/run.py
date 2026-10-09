"""Ejecuta el flujo completo aislado y detiene sus servidores al finalizar."""
import os
from pathlib import Path
import socket
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
TOOLS=os.environ.get('TEST_TOOLS_PATH','/tmp/muneco-verificacion')
TEMP=Path('/tmp/muneco-e2e'); TEMP.mkdir(exist_ok=True)
procesos=[]; archivos=[]
env={**os.environ,'TEST_TOOLS_PATH':TOOLS,'VITE_API_URL':'http://127.0.0.1:5059'}

def esperar(puerto):
    for _ in range(60):
        try:
            with socket.create_connection(('127.0.0.1',puerto),timeout=1): return
        except OSError: time.sleep(0.5)
    raise RuntimeError(f'El servidor del puerto {puerto} no inició. Revise {TEMP}.')

def iniciar(args,nombre,cwd=ROOT):
    archivo=(TEMP/(nombre+'.log')).open('w'); archivos.append(archivo)
    p=subprocess.Popen(args,cwd=cwd,env=env,stdout=archivo,stderr=subprocess.STDOUT); procesos.append(p)

try:
    iniciar(['node','backend/tests/e2e/bridge.mjs'],'postgres'); esperar(54329)
    iniciar([str(ROOT/'backend/venv/bin/python'),'backend/tests/e2e/server.py'],'flask'); esperar(5059)
    iniciar(['pnpm','dev','--host','127.0.0.1','--port','5179','--strictPort'],'vite',ROOT/'frontend'); esperar(5179)
    resultado=subprocess.run(['node',TOOLS+'/node_modules/@playwright/test/cli.js','test',
        '--config',str(ROOT/'frontend/tests/playwright.config.cjs')],cwd=ROOT,env=env)
    raise SystemExit(resultado.returncode)
finally:
    for p in reversed(procesos):
        p.terminate()
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill()
    for archivo in archivos: archivo.close()
