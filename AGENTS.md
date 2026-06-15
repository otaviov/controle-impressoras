## Goal
Implementar agenda do técnico com visão diária, rota sugerida por setor, capacidade de atendimento e histórico de produtividade; refinar especialidades (por modelo de impressora) e permitir abrir OS por clique no histórico.

## Constraints & Preferences
- Especialidades devem ser por **modelo de impressora** (ex.: "HP M425"), não por equipamento específico
- Duplo clique em OS nas tabelas do Histórico deve abrir o detalhe da OS
- Agenda por técnico: ver OS do dia com ordem de rota agrupada por `from_location`
- Capacidade diária do técnico: campo `capacidade_diaria` (default 5)
- Produtividade: OS de manutenção concluídas com contagem, peças usadas, tempo médio
- Sessões: permitir associar manualmente um usuário do sistema ao técnico via combo + salvar

## Progress
### Done
- Galeria de fotos nas OS com abas, upload, carrossel, exclusão, refresh automático
- Fluxo de status expandido: Aberta → Aguardando Peça → Técnico Designado → Em Deslocamento → Em Manutenção → Em Atendimento → Aguardando Aprovação → Concluido → Verificada
- "Concluir OS" visível para todos os status exceto Concluido/Verificada
- Programação de manutenção recorrente (período e páginas) com calendário visual, alertas antecipados e geração automática de OS
- Botão "🗑️ Apagar" em programações recorrentes com confirmação
- 4 migrações Alembic: `capacidade_diaria`, `user_id` em technicians, M2M `technician_specialties`, refactor para modelo string
- Modelo `Technician`: campos `capacidade_diaria` (Integer, default 5) e `user_id` (FK → users.id)
- Modelo `TechnicianSpecialty`: `(id, technician_id, modelo TEXT)` substituindo antiga M2M com `printer_id`
- `TechnicianAgendaPage`: seletor técnico + data, cards de capacidade, tabela com rota sugerida, aba de produtividade com filtro por período, tempo médio e peças
- `TechnicianHistoryPage` expandida: aba "OS Abertas" (não concluídas em tempo real), aba "Peças" (top peças do técnico + busca "quem usou tal peça")
- Barra de associação de usuário na aba Sessões (combo + salvar), com auto-associação por nome e fallback manual
- Métodos em `activity_service`: `listar_por_tecnico_e_data`, `contar_por_tecnico_por_data`, `listar_concluidas_por_tecnico_no_periodo`, `listar_os_abertas_por_tecnico`, `listar_pecas_por_tecnico`, `listar_tecnicos_por_peca`
- Métodos em `technician_service`: `associar_usuario`, `listar_especialidades`, `adicionar_especialidades`, `remover_especialidades`, `limpar_especialidades` — agora baseados em `modelo` (string)
- Sinal `abrir_os` em `TechnicianHistoryPage` emitido no duplo clique das tabelas (Atividades, Em Andamento, OS Abertas), conectado no `main_window.py` ao handler `_abrir_atividade_por_id`
- `_EspecialidadesDialog` refatorado: mostra modelos distintos do banco + campo para digitar modelo livre
- 137 testes passando (1 falha pré-existente `test_very_long_password`)

### In Progress
- *(none)*

### Blocked
- *(none)*

## Key Decisions
- Especialidades mudaram de "impressora específica (patrimônio)" para "modelo de impressora (string)" — mais útil no dia a dia
- Tabela `technician_specialties` refatorada de `(technician_id, printer_id)` para `(technician_id, modelo)` sem FK para `printers`
- Duplo clique nas linhas de OS emite sinal `abrir_os(activity_id)` conectado no `main_window.py` para navegar para página de OS
- A associação técnico ↔ usuário é persistida via `technician.user_id`, permitindo consulta direta de sessões sem matching por nome
- `TechnicianAgendaPage` usa `from_location` para agrupar OS em rota sugerida

## Next Steps
- *(nenhum)*

## Critical Context
- `Technician` já tem `user_id` (FK → users.id) e `capacidade_diaria`
- `technician_specialties` agora é tabela `(id, technician_id, modelo TEXT)` — não há mais FK para `printers`
- `Printer.specialist_technicians` removido — não faz mais sentido com modelo string
- `TechnicianHistoryPage` emite sinal `abrir_os` ao dar duplo clique nas linhas de OS
- `main_window.py` conecta `pagina_historico.abrir_os` ao mesmo handler `_abrir_atividade_por_id`

## Relevant Files
- `app/models/technician_specialty.py`: novo modelo ORM com `technician_id` e `modelo` (string)
- `app/models/technician.py`: `specialties: Mapped[List[TechnicianSpecialty]]`
- `app/models/printer.py`: `specialist_technicians` removido
- `app/models/__init__.py`: exporta `TechnicianSpecialty`
- `alembic/versions/f6a7b8c9d0e1_refactor_technician_specialties.py`: migração que recria tabela
- `app/services/technician_service.py`: métodos de especialidades refatorados para modelo string
- `app/services/activity_service.py`: métodos para OS abertas, peças por técnico, peças por busca
- `app/views/pages/technicians_page.py`: `_EspecialidadesDialog` refatorado (mostra modelos + input livre); `_detalhes` exibe modelos
- `app/views/pages/technician_history_page.py`: sinal `abrir_os`; `cellDoubleClicked` nas 3 tabelas; `activity_id` armazenado via `Qt.UserRole`
- `app/views/main_window.py`: `pagina_historico.abrir_os.connect(...)`
