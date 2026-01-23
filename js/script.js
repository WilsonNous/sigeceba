// js/script.js

// ============================
// Helpers
// ============================
function byId(id) { return document.getElementById(id); }
function qs(sel) { return document.querySelector(sel); }
function qsa(sel) { return document.querySelectorAll(sel); }

// Função para mostrar/ocultar seções
function showSection(sectionId) {
    qsa('.form-section').forEach(section => {
        section.classList.add('hidden');
    });
    qsa('nav button').forEach(button => {
        button.classList.remove('active');
    });

    const sec = byId(sectionId);
    if (sec) sec.classList.remove('hidden');

    const navBtn = byId('nav' + sectionId.charAt(0).toUpperCase() + sectionId.slice(1));
    if (navBtn) navBtn.classList.add('active');

    // Carregar dados específicos ao abrir a seção
    if (sectionId === 'dashboard') carregarDashboard();
    if (sectionId === 'entregas') carregarFamiliasSelect();
    if (sectionId === 'consulta') buscarFamilias();
    if (sectionId === 'historico') {
        carregarFamiliasFiltro();
        filtrarEntregas();
    }

    // ✅ NOVAS ABAS
    if (sectionId === 'insumos') {
        carregarInsumos();
    }
    if (sectionId === 'kits') {
        // para montar selects e tabelas
        carregarInsumos();
        carregarKits();
    }
}

// ============================
// Calcular idade
// ============================
const nascimentoEl = byId('responsavelNascimento');
if (nascimentoEl) {
    nascimentoEl.addEventListener('change', function() {
        const nascimento = new Date(this.value);
        const hoje = new Date();
        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const mes = hoje.getMonth() - nascimento.getMonth();
        if (mes < 0 || (mes === 0 && hoje.getDate() < nascimento.getDate())) idade--;
        const idadeEl = byId('responsavelIdade');
        if (idadeEl) idadeEl.value = idade;
    });
}

// Limpar formulário
function limparFormulario() {
    const form = byId('familiaForm');
    if (form && confirm('Tem certeza que deseja limpar o formulário?')) {
        form.reset();
    }
}

// Data atual para entrega
const dataEntregaEl = byId('dataEntrega');
if (dataEntregaEl) dataEntregaEl.valueAsDate = new Date();

// ============================
// CADASTRAR FAMÍLIA
// ============================
const familiaForm = byId('familiaForm');
if (familiaForm) {
    familiaForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch('/cadastrar-familia', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                alert('Cadastro salvo com sucesso!');
                this.reset();
                showSection('dashboard');
            } else {
                alert(`Erro: ${result.error || 'Não foi possível salvar.'}`);
            }
        } catch (err) {
            alert('Erro de conexão com o servidor.');
            console.error(err);
        }
    });
}

// ============================
// REGISTRAR ENTREGA
// ============================
const entregaForm = byId('entregaForm');
if (entregaForm) {
    entregaForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch('/registrar-entrega', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                alert('Entrega registrada com sucesso!');
                this.reset();
                const d = byId('dataEntrega');
                if (d) d.valueAsDate = new Date();
                showSection('dashboard');
            } else {
                const result = await response.json();
                alert(`Erro: ${result.error}`);
            }
        } catch (err) {
            alert('Erro de conexão com o servidor.');
            console.error(err);
        }
    });
}

// ============================
// CARREGAR DASHBOARD
// ============================
async function carregarDashboard() {
    try {
        const response = await fetch('/dashboard-data');
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const data = await response.json();

        byId('totalFamilias').textContent = data.totalFamilias;
        byId('cestasMes').textContent = data.cestasMes;
        byId('totalPessoas').textContent = data.totalPessoas;
        byId('cestasEstoque').textContent = data.cestasEstoque;

        const tbody = qs('#ultimasEntregas tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        (data.ultimasEntregas || []).forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${e.data}</td>
                <td>${e.familia}</td>
                <td>${e.responsavel}</td>
                <td>${e.quantidade}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Erro ao carregar dashboard:', err);
        alert('Erro ao carregar dados do dashboard.');
    }
}

// ============================
// BUSCAR FAMÍLIAS
// ============================
async function buscarFamilias() {
    const buscaEl = byId('buscaFamilia');
    const query = buscaEl ? buscaEl.value.trim() : '';
    const url = `/buscar-familias${query ? `?q=${encodeURIComponent(query)}` : ''}`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const familias = await response.json();

        const tbody = qs('#tabelaFamilias tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!familias || familias.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">Nenhuma família encontrada.</td></tr>';
            return;
        }

        familias.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${f.responsavel_nome}</td>
                <td>${f.cpf}</td>
                <td>${f.telefone || '—'}</td>
                <td>${f.numero_pessoas}</td>
                <td>—</td>
                <td>
                    <button class="btn-primary" onclick="editarFamilia(${f.id})">Editar</button>
                    <button class="btn-secondary" onclick="detalhesFamilia(${f.id})">Detalhes</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        alert('Erro ao buscar famílias.');
        console.error(err);
    }
}

// FUNÇÕES DE AÇÃO DA TABELA
function editarFamilia(id) {
    alert(`Editar família ID: ${id}`);
    // Futuro: carregar dados e preencher formulário
}

function detalhesFamilia(id) {
    fetch(`/buscar-familias?q=${id}`)
        .then(r => r.json())
        .then(familias => {
            const f = familias[0];
            if (f) {
                let mensagem = `Detalhes da Família\n\n`;
                mensagem += `Responsável: ${f.responsavel_nome}\n`;
                mensagem += `CPF: ${f.cpf}\n`;
                mensagem += `Telefone: ${f.telefone}\n`;
                mensagem += `Membros na casa: ${f.numero_pessoas}\n`;
                mensagem += `Filhos: ${f.numero_filhos || 0}\n`;
                alert(mensagem);
            }
        })
        .catch(err => {
            alert("Erro ao carregar detalhes da família.");
            console.error(err);
        });
}

// ============================
// POPULAR SELECT DE ENTREGA
// ============================
async function carregarFamiliasSelect() {
    try {
        const response = await fetch('/buscar-familias');
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const familias = await response.json();

        const select = byId('familiaEntrega');
        if (!select) return;

        select.innerHTML = '<option value="">Selecione uma família</option>';

        (familias || []).forEach(f => {
            const option = document.createElement('option');
            option.value = f.id;
            option.textContent = `${f.responsavel_nome} (${f.cpf})`;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Erro ao carregar famílias para select:', err);
    }
}

// ============================
// FILTRAR ENTREGAS
// ============================
async function filtrarEntregas() {
    const dataInicio = byId('dataInicio')?.value || '';
    const dataFim = byId('dataFim')?.value || '';
    const familia = byId('familiaFiltro')?.value || '';

    let url = '/listar-entregas?';
    if (dataInicio) url += `dataInicio=${dataInicio}&`;
    if (dataFim) url += `dataFim=${dataFim}&`;
    if (familia) url += `familia=${familia}&`;
    url = url.endsWith('?') ? '/listar-entregas' : url.slice(0, -1);

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const entregas = await response.json();

        const tbody = qs('#tabelaEntregas tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        (entregas || []).forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${e.data_entrega}</td>
                <td>${e.familia_nome}</td>
                <td>${e.responsavel}</td>
                <td>${e.quantidade}</td>
                <td>${e.responsavel_entrega}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Erro ao filtrar entregas:', err);
    }
}

// ============================
// POPULAR FILTRO DE FAMÍLIAS NO HISTÓRICO
// ============================
async function carregarFamiliasFiltro() {
    try {
        const response = await fetch('/buscar-familias');
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const familias = await response.json();

        const select = byId('familiaFiltro');
        if (!select) return;

        select.innerHTML = '<option value="">Todas as famílias</option>';

        (familias || []).forEach(f => {
            const option = document.createElement('option');
            option.value = f.id;
            option.textContent = f.responsavel_nome;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Erro ao carregar famílias no filtro:', err);
    }
}

// ============================
// LIMPAR BUSCA
// ============================
function limparBusca() {
    const el = byId('buscaFamilia');
    if (el) el.value = '';
    buscarFamilias();
}

// =====================================================
// ✅ INSUMOS
// =====================================================
async function carregarInsumos() {
    try {
        const res = await fetch('/insumos');
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        const data = await res.json();

        // tabela insumos
        const tbody = qs('#tabelaInsumos tbody');
        if (tbody) {
            tbody.innerHTML = '';
            (data || []).forEach(i => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i.id}</td>
                    <td>${i.nome}</td>
                    <td>${i.unidade}</td>
                    <td>${i.ativo ? 'Sim' : 'Não'}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // select insumos na aba kits
        const sel = byId('insumoSelect');
        if (sel) {
            sel.innerHTML = `<option value="">Selecione...</option>`;
            (data || []).forEach(i => {
                const opt = document.createElement('option');
                opt.value = i.id;
                opt.textContent = `${i.nome} (${i.unidade})`;
                sel.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Erro ao carregar insumos:', err);
    }
}

const insumoForm = byId('insumoForm');
if (insumoForm) {
    insumoForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nome = byId('insumoNome')?.value?.trim() || '';
        const unidade = byId('insumoUnidade')?.value?.trim() || '';

        if (!nome || !unidade) {
            alert('Informe nome e unidade.');
            return;
        }

        try {
            const res = await fetch('/insumos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome, unidade })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                alert(err.error || 'Erro ao salvar insumo.');
                return;
            }

            alert('Insumo salvo!');
            insumoForm.reset();
            await carregarInsumos();
        } catch (err) {
            console.error(err);
            alert('Erro de conexão ao salvar insumo.');
        }
    });
}

// =====================================================
// ✅ KITS
// =====================================================
async function carregarKits() {
    try {
        const res = await fetch('/kits');
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        const data = await res.json();

        // tabela kits
        const tbody = qs('#tabelaKits tbody');
        if (tbody) {
            tbody.innerHTML = '';
            (data || []).forEach(k => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${k.id}</td>
                    <td>${k.nome}</td>
                    <td>${k.descricao || ''}</td>
                    <td>${k.ativo ? 'Sim' : 'Não'}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // select de kits
        const sel = byId('kitSelect');
        if (sel) {
            const current = sel.value;
            sel.innerHTML = `<option value="">Selecione...</option>`;
            (data || []).forEach(k => {
                const opt = document.createElement('option');
                opt.value = k.id;
                opt.textContent = k.nome;
                sel.appendChild(opt);
            });
            // tenta manter o kit selecionado
            if (current) sel.value = current;
        }

    } catch (err) {
        console.error('Erro ao carregar kits:', err);
    }
}

const kitForm = byId('kitForm');
if (kitForm) {
    kitForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nome = byId('kitNome')?.value?.trim() || '';
        const descricao = byId('kitDescricao')?.value?.trim() || '';

        if (!nome) {
            alert('Informe o nome do kit.');
            return;
        }

        try {
            const res = await fetch('/kits', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome, descricao })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                alert(err.error || 'Erro ao salvar kit.');
                return;
            }

            alert('Kit salvo!');
            kitForm.reset();
            await carregarKits();
        } catch (err) {
            console.error(err);
            alert('Erro de conexão ao salvar kit.');
        }
    });
}

async function carregarItensDoKit() {
    const kitId = byId('kitSelect')?.value;
    if (!kitId) {
        alert('Selecione um kit para ver os itens.');
        return;
    }

    try {
        const res = await fetch(`/kits/${kitId}/itens`);
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        const data = await res.json();

        const tbody = qs('#tabelaKitItens tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        (data || []).forEach(it => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${it.item_id}</td>
                <td>${it.insumo_nome}</td>
                <td>${it.quantidade}</td>
                <td>${it.unidade}</td>
                <td>
                    <button class="btn-secondary" onclick="removerItemKit(${it.item_id})">Remover</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error('Erro ao carregar itens do kit:', err);
        alert('Erro ao carregar itens do kit.');
    }
}

async function removerItemKit(itemId) {
    if (!confirm('Remover este item do kit?')) return;

    try {
        const res = await fetch(`/kits/itens/${itemId}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            alert(err.error || 'Erro ao remover item.');
            return;
        }
        await carregarItensDoKit();
    } catch (err) {
        console.error(err);
        alert('Erro de conexão ao remover item.');
    }
}

const kitItemForm = byId('kitItemForm');
if (kitItemForm) {
    kitItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const kitId = byId('kitSelect')?.value;
        const insumoId = byId('insumoSelect')?.value;
        const qtdStr = byId('itemQtd')?.value;

        if (!kitId) { alert('Selecione um kit.'); return; }
        if (!insumoId) { alert('Selecione um insumo.'); return; }

        const qtd = Number(qtdStr);
        if (!qtd || qtd <= 0) { alert('Quantidade deve ser maior que 0.'); return; }

        try {
            const res = await fetch(`/kits/${kitId}/itens`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ insumo_id: insumoId, quantidade: qtd })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                alert(err.error || 'Erro ao adicionar item no kit.');
                return;
            }

            alert('Item adicionado/atualizado no kit!');
            // não reseta kitSelect, só quantidade
            if (byId('itemQtd')) byId('itemQtd').value = '';
            await carregarItensDoKit();
        } catch (err) {
            console.error(err);
            alert('Erro de conexão ao adicionar item.');
        }
    });
}

// Se trocar o kit selecionado, recarrega itens automaticamente
const kitSelect = byId('kitSelect');
if (kitSelect) {
    kitSelect.addEventListener('change', () => {
        const val = kitSelect.value;
        const tbody = qs('#tabelaKitItens tbody');
        if (tbody) tbody.innerHTML = '';
        if (val) carregarItensDoKit();
    });
}

// ============================
// Carregar dashboard ao iniciar
// ============================
document.addEventListener('DOMContentLoaded', () => {
    carregarDashboard();
});

// =========================
// LOGOUT + INATIVIDADE (15 min)
// =========================
const IDLE_MINUTES = 15;
const IDLE_TIMEOUT_MS = IDLE_MINUTES * 60 * 1000;

let idleTimer = null;

async function logout() {
  try {
    // chama backend para limpar session
    await fetch("/api/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({})
    });
  } catch (e) {
    // mesmo que falhe, segue pra tela de login
    console.warn("Falha no logout (fetch). Redirecionando mesmo assim.", e);
  } finally {
    // limpa qualquer coisa local se você usar no futuro
    try { sessionStorage.removeItem("auth_token"); } catch (_) {}
    window.location.href = "/";
  }
}

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer);

  idleTimer = setTimeout(() => {
    alert("Sessão expirada por inatividade. Você será desconectado.");
    logout();
  }, IDLE_TIMEOUT_MS);
}

function initIdleLogout() {
  // eventos que contam como atividade
  const events = ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"];

  events.forEach(evt => {
    window.addEventListener(evt, resetIdleTimer, { passive: true });
  });

  // inicia o timer ao carregar
  resetIdleTimer();
}

// inicializa junto com o dashboard
document.addEventListener("DOMContentLoaded", () => {
  initIdleLogout();
});

// =========================
// LOGOUT + INATIVIDADE (15 min) + TOAST
// =========================
const IDLE_MINUTES = 15;
const IDLE_TIMEOUT_MS = IDLE_MINUTES * 60 * 1000;

let idleTimer = null;
let countdownTimer = null;
let idleDeadline = null;

function showToast(message, subMessage = "", ms = 3500) {
  const el = document.getElementById("toast");
  if (!el) return;

  el.innerHTML = `
    <div>${message}</div>
    ${subMessage ? `<small>${subMessage}</small>` : ""}
  `;
  el.classList.remove("hidden");

  clearTimeout(el._hideTimer);
  el._hideTimer = setTimeout(() => {
    el.classList.add("hidden");
  }, ms);
}

function formatMMSS(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

async function logout() {
  try {
    await fetch("/api/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({})
    });
  } catch (e) {
    console.warn("Falha no logout (fetch). Redirecionando mesmo assim.", e);
  } finally {
    window.location.href = "/";
  }
}

function stopIdleTimers() {
  if (idleTimer) clearTimeout(idleTimer);
  if (countdownTimer) clearInterval(countdownTimer);
  idleTimer = null;
  countdownTimer = null;
}

function startCountdown() {
  clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    const remaining = idleDeadline - Date.now();
    // Só mostra quando estiver a menos de 1 minuto
    if (remaining <= 60 * 1000 && remaining > 0) {
      showToast(
        "Sessão prestes a expirar por inatividade.",
        `Saída automática em ${formatMMSS(remaining)}`
      );
    }
  }, 1000);
}

function resetIdleTimer() {
  stopIdleTimers();
  idleDeadline = Date.now() + IDLE_TIMEOUT_MS;

  // Reagenda logout
  idleTimer = setTimeout(() => {
    showToast("Sessão expirada por inatividade.", "Redirecionando para login...", 2000);
    setTimeout(() => logout(), 800);
  }, IDLE_TIMEOUT_MS);

  // Começa contagem (só avisa no último minuto)
  startCountdown();
}

function initIdleLogout() {
  const events = ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"];
  events.forEach(evt => window.addEventListener(evt, resetIdleTimer, { passive: true }));
  resetIdleTimer();
}

document.addEventListener("DOMContentLoaded", () => {
  initIdleLogout();
});
