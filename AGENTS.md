## Goal
- Build a PyInstaller .exe for desktop installation while continuing incremental UI/UX improvements.

## Constraints & Preferences
- Database goes to `%LOCALAPPDATA%\ControleImpressoras\app.db` (separate from exe location)
- Bundled resources (themes, alembic, logo) found via `sys._MEIPASS` in frozen mode
- DB sem `alembic_version` é estampada automaticamente no head ao iniciar
- Mouse wheel must not change QComboBox, QDateEdit, QDateTimeEdit, or QTimeEdit values (global fix)
- Urgency field disabled when printer status is "Operacional" or "Em uso" (with red border indicator)
- Observations in printer detail must appear right below Identificação section
- Transfer cards (Total/Saídas/Entradas/Pendentes) must be clickable filters
- "Histórico Completo" checkbox in report dialog must be checked by default
- Observations shown in edit dialog must strip "Transferência —" / "Troca com X —" / "Peças para X —" prefix
- Pendentes filter filters by status "Aberta"
- Delete transfer must work without relying on TransferService (use direct soft-delete)

## Progress
### Done
- **(16) Executável + instalador**: PyInstaller onefile .exe com `install.ps1` que escolhe pasta, cria atalhos e registra em Add/Remove Programs
- **Global mouse‑wheel blocking**: `_NoWheelFilter` event filter em `main.py`
- **Histórico de Locais lê de Activity direto** — sincronizado com edições/exclusões
- **Removida criação de PrinterLocation** de `salvar_nova_silent` / `salvar_edicao` em transfers_page.py
- **activity_id FK em printer_locations** (migration `8a7b6c5d4e3f`)
- **Observações no detalhe da impressora** movido para abaixo da Identificação
- **Urgência bloqueada** quando status Operacional/Em uso
- **Cards clicáveis** (Total/Saídas/Entradas/Pendentes) com filtro por tipo
- **Relatório**: Histórico Completo marcado por padrão
- **Exclusão de transferência**: soft‑delete direto (`mov.deleted_at = dt.utcnow()`)
- **Campo Descrição** no edit dialog limpa prefixos (Transferência — / Troca com X — / Peças para X —)
- **Pendentes** filtrado por "Aberta"
- **`config.py`**: `DATA_DIR` = `%LOCALAPPDATA%\ControleImpressoras` (frozen) ou project root (dev); `BUNDLE_DIR` = `sys._MEIPASS` (frozen) ou project root (dev); `ANEXOS_DIR` e `BACKUP_DIR` usam `DATA_DIR`
- **`main.py`**: usa `BUNDLE_DIR` pra achar `alembic.ini`, themes e logo; estampa head se DB não tiver `alembic_version`
- **138 testes passando**

### In Progress
- *(none)*

### Blocked
- *(none)*

## Key Decisions
- **DATA_DIR separado do exe**: banco, anexos e backups vão pra `%LOCALAPPDATA%\ControleImpressoras` — permite instalar o .exe em Program Files sem precisar de permissão de escrita
- **BUNDLE_DIR** aponta pra `sys._MEIPASS` (temp dir do PyInstaller) onde ficam themes, alembic.ini e logo.png extraídos do onefile
- **DB sem alembic_version**: `main.py` detecta e estampa head antes de rodar upgrade — compatível com DBs de versões anteriores ao controle de migração
- **Instalador PowerShell**: sem dependência externa (Inno Setup/NSIS), funciona em qualquer Windows

## Next Steps
- *(nenhum)*

## Critical Context
- `config.py` exporta: `DATA_DIR`, `BUNDLE_DIR`, `BASE_DIR` (alias), `DB_PATH`, `BACKUP_DIR`, `ANEXOS_DIR`
- Em dev (não frozen): tudo aponta pra `Path(__file__).parent` (project root)
- Em frozen: `DATA_DIR` = `%LOCALAPPDATA%\ControleImpressoras`, `BUNDLE_DIR` = `sys._MEIPASS`
- Exe final: `dist/ControleImpressoras.exe` (~86 MB)
- Installer: `install.ps1` — mostra folder browser, copia exe, cria atalhos Desktop + Start Menu, registra em Add/Remove Programs
- O DB antigo em `%LOCALAPPDATA%\ControleImpressoras\app.db` (sem `alembic_version`) é automaticamente estampado e migrado na primeira execução
- 138 tests passam; App deve ser reiniciado pra pegar alterações de código

## Relevant Files
- `config.py` — DATA_DIR, BUNDLE_DIR, BASE_DIR, DB_PATH, BACKUP_DIR, ANEXOS_DIR
- `main.py` — alembic com suporte a DB legado, event filter NoWheelFilter, BUNDLE_DIR pra resources
- `install.ps1` — instalador com folder browser, shortcuts, Add/Remove Programs
- `app/views/pages/printers_page.py` — Observações movido, urgência bloqueada por status
- `app/views/pages/transfers_page.py` — cards clicáveis, exclusão direta, prefixo removido, ANEXOS_DIR do config
- `app/views/pages/os_page.py` — ANEXOS_DIR do config
- `app/views/relatorio_dialog.py` — checkbox Histórico Completo marcado por padrão
- `app/services/activity_service.py` — listar_movimentacoes_por_tipo / contar_por_tipo
- `dist/ControleImpressoras.exe` — executável único (~86 MB)
