## Goal
Implementar gestão de estoque completa: movimentações, reservas para OS, requisições de compra e histórico.

## Constraints & Preferences
- Toda movimentação de estoque deve gerar registro em `part_movements`
- Reservas de peças para OS diminuem o estoque e são consumidas ao concluir a OS
- Requisição de compra gerada automaticamente quando estoque < mínimo
- Botão "Receber Estoque" no detalhe da peça para entrada manual
- Requisições gerenciáveis via página dedicada

## Progress
### Done
- **(08) Geração automática de OS recorrentes** — por período e páginas
- **(09) Status expandido** — 9 estados (Aberta → ... → Verificada)
- **(10) Galeria de fotos** — upload, carrossel, abas antes/depois/peca
- **(11) Especialidades por modelo** — técnicos especializados em modelos de impressora (string)
- **(12) Agenda do técnico** — visão diária, rota por setor, capacidade, produtividade
- **(13) Histórico do técnico** — OS abertas, peças mais usadas, sessões, associação usuário
- **(14) Duplo clique abre OS** — nas 3 tabelas do histórico
- **(15) Migrations aplicadas** — `capacidade_diaria`, `user_id`, refactor specialties, estoque
- **137 testes passando** (1 falha pré-existente `test_very_long_password`)

### Estoque — Movimentações
- Modelo `PartMovement`: `(part_id, activity_id?, tipo, quantidade, saldo_anterior, saldo_posterior, observacao)`
- `PartService._log_movimento()` — registra qualquer alteração de estoque
- `PartService.receber_estoque()` — adiciona estoque com movimento tipo "entrada"
- `PartService.retirar_estoque()` — decrementa com movimento tipo "saida"
- `_dar_baixa_estoque()` atualizado em `os_page.py` e `transfers_page.py` — usa `retirar_estoque()` com `activity_id`
- `atualizar()` no `PartService` — ao alterar `quantidade_estoque`, registra movimento e cria requisição se necessário
- PartsPage detalhe: aba "Movimentações Recentes" (tabela com Data/Hora, Tipo, Qtd, Saldo, Observação)
- PartsPage: botão "📦 Receber Estoque" com diálogo de quantidade + observação

### Estoque — Reservas para OS
- Modelo `PartReservation`: `(part_id, activity_id, quantidade, status=reservada/usada/cancelada)`
- `PartService.criar_reserva()` — diminui estoque, cria movimento "reserva" e registro
- `PartService.usar_reserva()` — marca como "usada", cria movimento "saida"
- `PartService.cancelar_reserva()` — marca como "cancelada", restaura estoque, movimento "cancelamento_reserva"
- Diálogo "Concluir OS": botão "📌 Reservar" + tabela de reservas com botão "✕" para cancelar
- Diálogo "Editar OS": mesmo padrão com botão reservar + tabela
- Ao concluir OS: todas as reservas "reservada" são consumidas via `usar_reserva()`
- Detalhe da OS: mostra seção "Peças Reservadas" quando existem

### Estoque — Requisições de Compra
- Modelo `PurchaseRequisition`: `(part_id, quantidade_sugerida, status=pendente/aprovada/recebida/cancelada, observacao)`
- `PartService._criar_requisicao_auto()` — gera requisição quando estoque < mínimo (1 por peça, evita duplicatas pendentes)
- `PartService.aprovar_requisicao()`, `receber_requisicao()`, `cancelar_requisicao()`
- `receber_requisicao()` — automaticamente dá entrada no estoque
- `PurchaseRequisitionsPage`: tabela com filtro por status, botões Aprovar/Receber/Cancelar por linha
- Sidebar: link "🛒 Requisições" na seção Outros
- Detalhe da peça: mostra requisição pendente se existir

### In Progress
- *(none)*

### Blocked
- *(none)*

## Key Decisions
- `PartMovement`, `PartReservation`, `PurchaseRequisition` como tabelas separadas no banco (não text/json)
- Reserva já decrementa o estoque no momento da criação (estoque "comprometido")
- Cancelamento de reserva restaura o estoque automaticamente
- `_criar_requisicao_auto()` só cria se não houver outra pendente para a mesma peça
- `_dar_baixa_estoque()` nas OS agora usa `retirar_estoque()` que loga movimento + cria requisição
- Migração `7899a6741eeb` adiciona as 3 tabelas

## Next Steps
- *(nenhum)*

## Critical Context
- `PartService` agora gerencia movimentos e requisições de forma integrada
- `atualizar()` loga movimentos automaticamente ao mudar `quantidade_estoque`
- Reservas são consumidas automaticamente na conclusão da OS
- PurchaseRequisitionsPage registrada no sidebar como index 12
- Página de Requisições acessível por qualquer usuário (não só admin)

## Relevant Files
- `app/models/part_movement.py` — log de movimentações
- `app/models/part_reservation.py` — reservas para OS
- `app/models/purchase_requisition.py` — requisições de compra
- `app/services/part_service.py` — métodos de estoque, movimentos, reservas, requisições
- `app/views/pages/parts_page.py` — botão Receber Estoque + movimentações no detalhe
- `app/views/pages/os_page.py` — reservas no concluir/editar/detalhe
- `app/views/pages/purchase_requisitions_page.py` — página de gerenciamento
- `app/views/main_window.py` — registro da página e sidebar
- `alembic/versions/7899a6741eeb_add_part_movements_reservations_requisitions.py`
