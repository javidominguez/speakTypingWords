# Verbalización de palabras al escribir mejorada  

NVDA lee la palabra completa si se modifica, en lugar de sólo la parte añadida, que es el comportamiento predeterminado.

Este código ha sido extraído del complemento NVDAExtensionGlobalPlugin de Paulber19.
https://github.com/paulber19/NVDAExtensionGlobalPlugin
Según la Licencia Pública General GNU.
Todo el crédito pertenece a sus autores originales: Paulber19 y Leonardder.

La función que ejecuta este código se eliminó del complemento original en la versión 13.3; sin embargo, algunos usuarios la echan de menos. Este fork recupera la función adaptándola para que funcione de forma independiente en un pequeño complemento para esos usuarios.

Copyright de esta adaptación de Javi Domínguez (2024)

### Advertencias:  

* Si se está ejecutando una versión anterior a la 13.3 de NVDAExtensionGlobalPlugin y ha habilitado la opción eco por palabras mejorada, el manejo de dicha característica se delegará a ese complemento. Cuando la opción esté desactivada o NVDAExtensionGlobalPlugin se elimine/actualice, SpeakTypingWords tomará el control del eco por palabras.  
* Se han reportado errores al ejecutar esta función en Musescore que no se pudieron solucionar. Permanecerá deshabilitado en esa aplicación mientras no se solucionen los errores.  
* Algunos usuarios han reportado problemas al usar el eco por palabras mejorado con teclados Braille. No puedo asegurar que funcione correctamente con todos los dispositivos Braille.
