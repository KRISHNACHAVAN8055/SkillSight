(function() {
    function applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('skillsight-theme', theme);
    }

    function createToggle() {
        const btn = document.createElement('button');
        btn.id = 'theme-toggle-btn';
        btn.innerHTML = '🌙';
        btn.style.cssText = `
            position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px;
            border-radius: 50%; border: 1px solid var(--toggle-border, #e8e6e0);
            background: var(--toggle-bg, #fdfdfb); font-size: 26px; cursor: pointer;
            z-index: 2000; box-shadow: 0 4px 16px rgba(0,0,0,0.18);
            transition: transform 0.3s cubic-bezier(.34,1.56,.64,1), background 0.2s ease;
            display: flex; align-items: center; justify-content: center;
        `;
        btn.onmouseover = () => btn.style.transform = 'scale(1.08)';
        btn.onmouseout = () => btn.style.transform = 'scale(1)';
        btn.onclick = () => {
            const current = document.body.getAttribute('data-theme') || 'light';
            const next = current === 'light' ? 'dark' : 'light';
            btn.style.transform = 'scale(0.8) rotate(180deg)';
            setTimeout(() => {
                applyTheme(next);
                btn.innerHTML = next === 'light' ? '🌙' : '☀️';
                btn.style.transform = 'scale(1.15) rotate(360deg)';
                setTimeout(() => { btn.style.transform = 'scale(1) rotate(360deg)'; }, 150);
            }, 100);
        };
        document.body.appendChild(btn);

        const saved = localStorage.getItem('skillsight-theme') || 'light';
        applyTheme(saved);
        btn.innerHTML = saved === 'light' ? '🌙' : '☀️';
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createToggle);
    } else {
        createToggle();
    }
})();
