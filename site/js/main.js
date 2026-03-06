/* ============================================
   Melhor em Casa — Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Mobile Nav ---------- */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    navLinks.querySelectorAll('a').forEach(a =>
      a.addEventListener('click', () => navLinks.classList.remove('open'))
    );
  }

  /* ---------- Active Page Highlight ---------- */
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === page || (page === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });

  /* ---------- Lightbox ---------- */
  const overlay = document.getElementById('lightbox');
  if (overlay) {
    const lbImg = overlay.querySelector('img');

    document.querySelectorAll('.card img, img.zoomable').forEach(img => {
      img.style.cursor = 'zoom-in';
      img.addEventListener('click', () => {
        lbImg.src = img.src;
        lbImg.alt = img.alt;
        overlay.classList.add('active');
      });
    });

    overlay.addEventListener('click', () => overlay.classList.remove('active'));
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') overlay.classList.remove('active');
    });
  }

  /* ---------- Scroll-to-top ---------- */
  const scrollBtn = document.querySelector('.scroll-top');
  if (scrollBtn) {
    window.addEventListener('scroll', () => {
      scrollBtn.classList.toggle('visible', window.scrollY > 400);
    });
    scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  /* ---------- State Selector (estados page) ---------- */
  const stateSelect = document.getElementById('state-select');
  const stateDisplay = document.getElementById('state-display');
  const stateButtons = document.querySelectorAll('.state-btn');

  function showState(uf) {
    if (!stateDisplay) return;
    const imgPath = `Outputs%26Codigo/PARTE4/visualizacoes/estados/${uf}/${uf}_equipes_conformidade.png`;
    stateDisplay.innerHTML = `
      <div class="card card-full">
        <img src="${imgPath}" alt="Conformidade ${uf}" class="zoomable" />
        <div class="card-body">
          <h3>${uf} — Conformidade das Equipes</h3>
          <p>Distribuição de equipes conformes e não-conformes no estado, por tipo de equipe (Portaria 3.005/2024).</p>
        </div>
      </div>
    `;
    // Re-bind lightbox for dynamically added image
    const newImg = stateDisplay.querySelector('img');
    if (newImg && overlay) {
      const lbImg = overlay.querySelector('img');
      newImg.style.cursor = 'zoom-in';
      newImg.addEventListener('click', () => {
        lbImg.src = newImg.src;
        lbImg.alt = newImg.alt;
        overlay.classList.add('active');
      });
    }
    // Highlight active state button
    stateButtons.forEach(b => b.classList.toggle('active', b.dataset.uf === uf));
    if (stateSelect) stateSelect.value = uf;
  }

  if (stateSelect) {
    stateSelect.addEventListener('change', () => showState(stateSelect.value));
  }

  stateButtons.forEach(btn => {
    btn.addEventListener('click', () => showState(btn.dataset.uf));
  });

  // Default state
  if (stateDisplay && (stateSelect || stateButtons.length)) {
    showState('SP');
  }
});
