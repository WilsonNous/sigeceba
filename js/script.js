
// js/script.js

// Função para mostrar/ocultar seções
function showSection(sectionId) {
    document.querySelectorAll('.form-section').forEach(section => {
        section.classList.add('hidden');
    });
    document.querySelectorAll('nav button').forEach(button => {
        button.classList.remove('active');
    });
    document.getElementById(sectionId).classList.remove('hidden');
    document.getElementById('nav' + sectionId.charAt(0).toUpperCase() + sectionId.slice(1)).classList.add('active');

    // Carregar dados específicos ao abrir a seção
    if (sectionId === 'dashboard') carregarDashboard();
    if (sectionId === 'entregas') carregarFamiliasSelect();
    if (sectionId === 'consulta') buscarFamilias();
    if (sectionId === 'historico') {
        carregarFamiliasFiltro();
        filtrarEntregas();
    }
}

// Calcular idade
document.getElementById('responsavelNascimento').addEventListener('change', function() {
    const nascimento = new Date(this.value);
    const hoje = new Date();
    let idade = hoje.getFullYear() - nascimento.getFullYear();
    const mes = hoje.getMonth() - nascimento.getMonth();
    if (mes < 0 || (mes === 0 && hoje.getDate() < nascimento.getDate())) idade--;
    document.getElementById('responsavelIdade').value = idade;
});

// Limpar formulário
function limparFormulario() {
    if (confirm('Tem certeza que deseja limpar o formulário?')) {
        document.getElementById('familiaForm').reset();
    }
}

// Data atual para entrega
document.getElementById('dataEntrega').valueAsDate = new Date();

// === CADASTRAR FAMÍLIA ===
document.getElementById('familiaForm').addEventListener('submit', async function(e) {
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

// === REGISTRAR ENTREGA ===
document.getElementById('entregaForm').addEventListener('submit', async function(e) {
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
            document.getElementById('dataEntrega').valueAsDate = new Date();
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

// === CARREGAR DASHBOARD ===
async function carregarDashboard() {
    try {
        const response = await fetch('/dashboard-data');
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const data = await response.json();

        document.getElementById('totalFamilias').textContent = data.totalFamilias;
        document.getElementById('cestasMes').textContent = data.cestasMes;
        document.getElementById('totalPessoas').textContent = data.totalPessoas;
        document.getElementById('cestasEstoque').textContent = data.cestasEstoque;

        const tbody = document.querySelector('#ultimasEntregas tbody');
        tbody.innerHTML = '';
        data.ultimasEntregas.forEach(e => {
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

// === BUSCAR FAMÍLIAS ===
async function buscarFamilias() {
    const query = document.getElementById('buscaFamilia').value.trim();
    const url = `/buscar-familias${query ? `?q=${encodeURIComponent(query)}` : ''}`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const familias = await response.json();
        const tbody = document.querySelector('#tabelaFamilias tbody');
        tbody.innerHTML = '';

        if (familias.length === 0) {
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
                    <button class="btn-primary">Editar</button>
                    <button class="btn-secondary">Detalhes</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        alert('Erro ao buscar famílias.');
        console.error(err);
    }
}
// === FUNÇÕES PARA EDITAR E DETALHES ===

function editarFamilia(id) {
    alert(`Funcionalidade de edição da família ${id} será implementada.`);
    // Aqui você pode abrir um modal ou redirecionar para um formulário de edição
    // Ex: showSection('cadastro'); e preencher os campos
}

function detalhesFamilia(id) {
    // Busca os dados da família
    fetch(`/buscar-familias?q=${id}`)
        .then(r => r.json())
        .then(familias => {
            const f = familias[0];
            if (f) {
                alert(
                    `Detalhes da Família\n\n` +
                    `Responsável: ${f.responsavel_nome}\n` +
                    `CPF: ${f.cpf}\n` +
                    `Telefone: ${f.telefone}\n` +
                    `Membros: ${f.numero_pessoas}\n` +
                    `Observações: ${f.observacoes || '—'}`
                );
            }
        })
        .catch(err => {
            alert("Erro ao carregar detalhes.");
            console.error(err);
        });
}
// === POPULAR SELECT DE ENTREGA ===
async function carregarFamiliasSelect() {
    try {
        const response = await fetch('/buscar-familias');
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const familias = await response.json();
        const select = document.getElementById('familiaEntrega');
        select.innerHTML = '<option value="">Selecione uma família</option>';

        familias.forEach(f => {
            const option = document.createElement('option');
            option.value = f.id;
            option.textContent = `${f.responsavel_nome} (${f.cpf})`;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Erro ao carregar famílias para select:', err);
    }
}

// === FILTRAR ENTREGAS ===
async function filtrarEntregas() {
    const dataInicio = document.getElementById('dataInicio').value;
    const dataFim = document.getElementById('dataFim').value;
    const familia = document.getElementById('familiaFiltro').value;

    let url = '/listar-entregas?';
    if (dataInicio) url += `dataInicio=${dataInicio}&`;
    if (dataFim) url += `dataFim=${dataFim}&`;
    if (familia) url += `familia=${familia}&`;
    url = url.slice(0, -1); // Remove último &

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const entregas = await response.json();
        const tbody = document.querySelector('#tabelaEntregas tbody');
        tbody.innerHTML = '';

        entregas.forEach(e => {
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

// === POPULAR FILTRO DE FAMÍLIAS NO HISTÓRICO ===
async function carregarFamiliasFiltro() {
    try {
        const response = await fetch('/buscar-familias');
        if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
        const familias = await response.json();
        const select = document.getElementById('familiaFiltro');
        select.innerHTML = '<option value="">Todas as famílias</option>';

        familias.forEach(f => {
            const option = document.createElement('option');
            option.value = f.id;
            option.textContent = f.responsavel_nome;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Erro ao carregar famílias no filtro:', err);
    }
}

// === LIMPAR BUSCA ===
function limparBusca() {
    document.getElementById('buscaFamilia').value = '';
    buscarFamilias();
}

// Carregar dashboard ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    carregarDashboard();
});
