const apiBase = '/api';

async function loginUser(username, password) {
  const res = await fetch(`${apiBase}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  return res.json().then(data => ({ ok: res.ok, data }));
}

function saveToken(token) {
  localStorage.setItem('access_token', token);
}

function getToken() {
  return localStorage.getItem('access_token');
}

function logout() {
  localStorage.removeItem('access_token');
  window.location = '/';
}

async function fetchWithAuth(path, opts = {}) {
  const token = getToken();
  const headers = new Headers(opts.headers || {});
  headers.set('Accept', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  opts.headers = headers;
  const res = await fetch(`${apiBase}${path}`, opts);
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    if (res.status === 401) {
      logout();
    }
    const err = new Error('HTTP error ' + res.status);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

// Login form handler
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const res = await loginUser(username, password);
      if (res.ok) {
        saveToken(res.data.access_token);
        window.location = '/dashboard';
      } else {
        document.getElementById('error').textContent = res.data.error || 'Error en login';
      }
    });
  }

  // Logout button
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);

  // Dashboard data
  if (window.location.pathname === '/dashboard') {
    fetchWithAuth('/dashboard')
      .then(data => {
        if (data && data.resumen) {
          const resumen = document.getElementById('resumen');
          resumen.innerHTML = `<p>Total productos: ${data.resumen.total_productos}</p>
            <p>Valor inventario: ${data.resumen.valor_inventario}</p>
            <p>Movimientos hoy: ${data.resumen.movimientos_hoy}</p>`;

          const movList = document.getElementById('movimientosList');
          if (movList && Array.isArray(data.movimientos_recientes)) movList.innerHTML = data.movimientos_recientes.map(m => `<li>${m.motivo || ''} - ${m.cantidad || ''} - ${m.created_at || ''}</li>`).join('');

          const prodCrit = document.getElementById('productosCriticos');
          if (prodCrit && Array.isArray(data.productos_criticos)) prodCrit.innerHTML = data.productos_criticos.map(p => `<li>${p.nombre} - ${p.stock_actual}</li>`).join('');
        }
      })
      .catch(err => { console.error(err); });
  }

  // Productos page
  if (window.location.pathname === '/productos') {
    const list = document.getElementById('productosList');
    const search = document.getElementById('search');
    async function load(query=''){
      const q = query ? `?search=${encodeURIComponent(query)}` : '';
      try {
        const data = await fetchWithAuth(`/productos${q}`);
        if (data && Array.isArray(data.productos)) {
          list.innerHTML = data.productos.map(p => `<li>${p.codigo} - ${p.nombre} - Stock: ${p.stock_actual}</li>`).join('');
        } else {
          list.innerHTML = '<li>No hay productos o error al obtener datos</li>';
        }
      } catch (err) {
        console.error(err);
        list.innerHTML = `<li>Error: ${err.data && err.data.error ? err.data.error : err.message}</li>`;
      }
    }
    load();
    if (search) search.addEventListener('input', (e) => load(e.target.value));
  }

  // Movimientos page
  if (window.location.pathname === '/movimientos') {
    const list = document.getElementById('movimientosListPage');
    fetchWithAuth(`/movimientos?per_page=50`)
      .then(data => { if (data && Array.isArray(data.movimientos)) list.innerHTML = data.movimientos.map(m => `<li>${m.producto_nombre || m.producto_id} - ${m.cantidad} - ${m.motivo || ''} - ${m.created_at}</li>`).join(''); })
      .catch(err => { console.error(err); list.innerHTML = `<li>Error: ${err.data && err.data.error ? err.data.error : err.message}</li>`; });
  }

  // Reportes page
  if (window.location.pathname === '/reportes') {
    fetchWithAuth('/reportes/stock-categorias')
      .then(data => { const el = document.getElementById('stockCategorias'); if (el && Array.isArray(data)) el.innerHTML = data.map(c => `<li>${c.categoria} - Stock: ${c.stock_total} - Valor: ${c.valor_total}</li>`).join(''); })
      .catch(err => { console.error(err); const el = document.getElementById('stockCategorias'); if (el) el.innerHTML = `<li>Error: ${err.data && err.data.error ? err.data.error : err.message}</li>`; });

    fetchWithAuth('/reportes/productos-mas-vendidos')
      .then(data => { const el = document.getElementById('masVendidos'); if (el && Array.isArray(data)) el.innerHTML = data.map(p => `<li>${p.nombre} - Vendidos: ${p.total_vendido} - Ingresos: ${p.ingresos_totales}</li>`).join(''); })
      .catch(err => { console.error(err); const el = document.getElementById('masVendidos'); if (el) el.innerHTML = `<li>Error: ${err.data && err.data.error ? err.data.error : err.message}</li>`; });
  }
});
