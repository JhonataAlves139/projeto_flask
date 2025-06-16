// Controle das abas
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    // Remove active de todos
    tabButtons.forEach(b => b.classList.remove('active'));
    tabContents.forEach(tc => tc.classList.remove('active'));

    // Adiciona active na aba clicada
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// Recupera produtos do localStorage ou inicializa array vazio
let products = JSON.parse(localStorage.getItem('products')) || [];

// Função para atualizar tabela na aba Listar Produtos
function updateTable() {
  const tbody = document.querySelector('#productTable tbody');
  tbody.innerHTML = ''; // limpa tabela

  products.forEach(prod => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${prod.name}</td>
      <td>${prod.brand}</td>
      <td>${prod.batch}</td>
      <td>${prod.expiryDate}</td>
      <td>${prod.barcode}</td>
      <td>${prod.quantity}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Atualiza tabela ao carregar a página
updateTable();

// Limpar formulário ao clicar no botão "Limpar Campos"
document.getElementById('clearBtn').addEventListener('click', () => {
  document.getElementById('productForm').reset();
});

// Cadastrar produto
document.getElementById('productForm').addEventListener('submit', (e) => {
  e.preventDefault();

  // Pega valores dos inputs
  const name = document.getElementById('name').value.trim();
  const brand = document.getElementById('brand').value.trim();
  const batch = document.getElementById('batch').value.trim();
  const expiryDate = document.getElementById('expiryDate').value;
  const barcode = document.getElementById('barcode').value.trim();
  const quantity = document.getElementById('quantity').value;

  // Validação simples (já tem required no HTML, mas pode adicionar aqui se quiser)
  if (!name || !brand || !batch || !expiryDate || !barcode || !quantity) {
    alert('Por favor, preencha todos os campos.');
    return;
  }

  // Cria objeto produto
  const product = { name, brand, batch, expiryDate, barcode, quantity };

  // Adiciona ao array e salva no localStorage
  products.push(product);
  localStorage.setItem('products', JSON.stringify(products));

  // Atualiza tabela
  updateTable();

  // Limpa formulário
  e.target.reset();

  // Muda para aba de listagem automaticamente (opcional)
  tabButtons.forEach(b => b.classList.remove('active'));
  tabContents.forEach(tc => tc.classList.remove('active'));

  const listTabButton = document.querySelector('.tab-button[data-tab="list"]');
  listTabButton.classList.add('active');
  document.getElementById('list').classList.add('active');

  alert('Produto registrado com sucesso!');
});
