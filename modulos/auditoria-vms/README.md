# Auditoria de Tags de VMs

Modulo separado pela rota `/auditoria-vms`.

Ele compartilha, de forma intencional, a fotografia, os historicos, o cadastro de
subscriptions e os assets de `modulos/tags`, pois a auditoria e uma visao sobre
as mesmas VMs elegiveis da Governanca de Tags. Assim nao existem CSVs duplicados
nem duas fontes de verdade.

O ponto de entrada HTTP esta em `api/modulo_auditoria_vms_rotas.py`.
