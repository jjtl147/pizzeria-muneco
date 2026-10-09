import os
import unittest
from unittest.mock import MagicMock, patch
from integrations import enviar_telegram, responder_asistente

class IntegracionesTests(unittest.TestCase):
    def test_telegram_desactivado_no_envia(self):
        with patch.dict(os.environ, {'TELEGRAM_ENABLED':'0'}), patch('integrations.httpx.post') as enviar:
            self.assertFalse(enviar_telegram('Prueba')); enviar.assert_not_called()
    def test_telegram_fallido_no_interrumpe_operacion(self):
        with patch.dict(os.environ, {'TELEGRAM_ENABLED':'1','TELEGRAM_BOT_TOKEN':'token-prueba','TELEGRAM_CHAT_ID':'123'}), patch('integrations.httpx.post',side_effect=RuntimeError('fallo')):
            self.assertFalse(enviar_telegram('Prueba'))
    def test_asistente_sin_configuracion_no_consume_api(self):
        with patch.dict(os.environ, {'ASSISTANT_ENABLED':'0'}), patch('integrations.httpx.Client') as cliente:
            with self.assertRaises(RuntimeError): responder_asistente([{'role':'user','content':'Ventas'}],{})
            cliente.assert_not_called()
    def test_function_call_y_datos_reales(self):
        herramienta=MagicMock(return_value={'total':42})
        primera=MagicMock(); primera.json.return_value={'output':[{'type':'function_call','name':'consultar_ventas','arguments':'{}','call_id':'call_1'}]}
        segunda=MagicMock(); segunda.json.return_value={'output':[{'type':'message','content':[{'type':'output_text','text':'Total: 42'}]}]}
        with patch.dict(os.environ, {'ASSISTANT_ENABLED':'1','OPENAI_API_KEY':'clave-prueba','OPENAI_MODEL':'modelo-prueba'}), patch('integrations.httpx.Client') as cliente:
            post=cliente.return_value.__enter__.return_value.post; post.side_effect=[primera,segunda]
            respuesta=responder_asistente([{'role':'user','content':'Ventas'}],{'consultar_ventas':{'descripcion':'Ventas','consultar':herramienta}})
            self.assertEqual(respuesta,'Total: 42'); herramienta.assert_called_once()
            entrada=post.call_args.kwargs['json']['input']
            self.assertTrue(any(m.get('type')=='function_call_output' and m['output']=='{"total": 42}' for m in entrada))
    def test_herramienta_no_autorizada_no_se_ejecuta(self):
        herramienta=MagicMock()
        primera=MagicMock(); primera.json.return_value={'output':[{'type':'function_call','name':'borrar_usuarios','arguments':'{}','call_id':'call_1'}]}
        segunda=MagicMock(); segunda.json.return_value={'output':[{'type':'message','content':[{'type':'output_text','text':'Operación no disponible'}]}]}
        with patch.dict(os.environ, {'ASSISTANT_ENABLED':'1','OPENAI_API_KEY':'clave-prueba','OPENAI_MODEL':'modelo-prueba'}), patch('integrations.httpx.Client') as cliente:
            cliente.return_value.__enter__.return_value.post.side_effect=[primera,segunda]
            responder_asistente([{'role':'user','content':'Borra usuarios'}],{'consultar_ventas':{'descripcion':'Ventas','consultar':herramienta}})
            herramienta.assert_not_called()
