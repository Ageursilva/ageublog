document.addEventListener('DOMContentLoaded', () => {
    const searchIcon = document.querySelector('.search-link'); // Mudei aqui

    if (searchIcon) { // Verifica se o elemento existe
        searchIcon.addEventListener('click', (e) => {
            e.preventDefault(); // Previne o comportamento padrão do link

            // Verifica se o formulário já foi inserido
            if (!document.querySelector('.search-form')) {
                // Cria o formulário de pesquisa
                const searchForm = document.createElement('form');
                searchForm.classList.add('search-form');
                searchForm.setAttribute('action', '/search');
                searchForm.setAttribute('method', 'GET');

                const searchInput = document.createElement('input');
                searchInput.type = 'text';
                searchInput.name = 'query';
                searchInput.placeholder = 'Pesquisar...';
                searchInput.classList.add('search-input');

                const searchButton = document.createElement('button');
                searchButton.type = 'submit';
                searchButton.textContent = 'Buscar';
                searchButton.classList.add('search-button');

                // Adiciona o campo de texto e o botão ao formulário
                searchForm.appendChild(searchInput);
                searchForm.appendChild(searchButton);

                // Insere o formulário logo após o nav
                const nav = document.querySelector('nav');
                nav.after(searchForm);

                // Foca no input
                searchInput.focus();
            }
        });
    }
});
