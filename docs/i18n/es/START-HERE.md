# Empieza aquí: tu primer camino en OCI

Guía breve en español, revisión **2026-09-19**, alineada con la
[guía canónica en inglés](../../GETTING-STARTED.md) de esta misma revisión.
Es un punto de entrada mantenido, no una traducción completa de la documentación.
Los comandos, límites de ejecución y procedimientos permanecen en las guías
canónicas; revisa este resumen cuando cambien.

Founder Toolkit for OCI es un proyecto personal independiente de Daniel Gandolfi,
quien trabaja en Oracle y publica a título personal. No es un producto Oracle,
no representa a la empresa y no ofrece soporte de Oracle ni un SLA.

## ¿Qué resultado necesitas ahora?

| Tu situación | Empieza por | Resultado esperado |
|---|---|---|
| Trabajo solo y quiero entender OCI | [Quickstart](../../QUICKSTART.md) | Una recomendación para tu backend, supuestos, costos por investigar y siguiente paso |
| Tenemos un equipo pequeño | [Baseline](../../FOUNDER-BASELINE.md) | Plan con responsables de despliegue, acceso, costos e incidentes |
| Ya uso AWS, GCP o Azure | [Casos de uso](../../USE-CASES.md) | Correspondencias entre servicios y diferencias que probar antes de migrar |
| Necesito atender al primer cliente | [Backend de referencia](../../REFERENCE-BACKEND.md) | Lista de seguridad, operación, costo y evidencias para decidir si avanzar |

## Sigue el orden que corresponde a tu necesidad

1. **Instala en un repositorio y para un agente.** Sigue los comandos del
   [quickstart](../../QUICKSTART.md); el primer análisis no requiere una cuenta
   OCI. No copies credenciales al chat.
2. **Prepara tu cuenta cuando necesites usarla.** La guía de
   [acceso local](../../ACCOUNT-SETUP.md) muestra dónde encontrar los OCID,
   cómo elegir la autenticación y cómo ejecutar una consulta de solo lectura.
3. **Aprende VCN, subnet y VM.** Ejecuta personalmente el
   [laboratorio de VM Linux](../../FIRST-VM.md), revisando red, SSH, costo y
   recursos exactos antes de crear o eliminar cualquier elemento.
4. **Planifica el producto.** Consulta el [backend de referencia](../../REFERENCE-BACKEND.md)
   y los [escenarios de costo](../../COST-SCENARIOS.md). Usa la guía de
   [evidencias](../../EVIDENCE.md) para distinguir lo documentado, lo probado
   localmente y lo realmente ejecutado en OCI.

El skill independiente **v0.1.1** se limita a planificación sin sus dependencias
operativas verificadas. Instalarlo no autentica tu terminal, no concede permisos
IAM y no automatiza el laboratorio. El backend de referencia es un diseño de
arquitectura, no un producto ya desplegado y validado en producción.

## Cuenta, pago y región: decisiones tuyas

Si tu empresa ya usa OCI, pide al administrador el acceso y el compartment
correctos. Para una cuenta nueva, consulta las
[preguntas frecuentes oficiales de registro](https://www.oracle.com/cloud/free/faq/):
las condiciones, los países, los medios de pago y la capacidad pueden variar.
Este proyecto no garantiza créditos, elegibilidad, recursos gratuitos
disponibles ni costo cero.

El registro y la actualización a una cuenta de pago son decisiones separadas.
Revisa los términos y confirma personalmente cualquier contratación o cambio
financiero; no autorices una actualización solo para evitar un error. Nunca
envíes una tarjeta, contraseña, código MFA o clave privada al agente. Consulta
los detalles en la [guía canónica](../../GETTING-STARTED.md).

Elige la región según tus clientes, la latencia medida, los servicios necesarios,
los backups y los requisitos de ubicación de datos. No supongas que una misma
región sirve para toda América Latina ni que garantiza cumplimiento legal.
La [home region no puede cambiarse después del aprovisionamiento](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingregions.htm);
revisa esa decisión antes del registro. Confirma la disponibilidad actual y los
requisitos con los responsables de tu empresa.

## ¿Te bloqueaste? Busca ayuda según el problema

- **Registro, pago, acceso o MFA:** utiliza las
  [rutas oficiales de recuperación y chat](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signinginIdentityDomain.htm).
- **El agente no encuentra el skill:** sigue el diagnóstico del quickstart;
  después consulta el [soporte del proyecto](../../../SUPPORT.md).
- **CLI, región o IAM:** sigue la guía de acceso y consulta al administrador;
  no solicites permisos administrativos generales para hacer funcionar el ejemplo.
- **VM, SSH o red:** sigue el diagnóstico del laboratorio y comprueba los datos
  de la instancia; no abras SSH a todo internet como intento de solución.

Los problemas del servicio OCI siguen las [opciones oficiales de soporte](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport.htm)
disponibles para tu cuenta. Las issues del proyecto reciben ayuda comunitaria
sin SLA y no sustituyen el soporte contratado. Elimina secretos, datos de
clientes e identificadores privados de cualquier informe público. Para fallos
de seguridad, sigue [SECURITY.md](../../../SECURITY.md).
