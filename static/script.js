document.addEventListener('DOMContentLoaded', () => {
    const searchIcon = document.querySelector('.search-icon');

    searchIcon.addEventListener('click', () => {
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
            
            const searchButton = document.createElement('button');
            searchButton.type = 'submit';
            searchButton.textContent = 'Buscar';
            
            // Adiciona o campo de texto e o botão ao formulário
            searchForm.appendChild(searchInput);
            searchForm.appendChild(searchButton);

            // Insere o formulário logo após o ícone de pesquisa
            searchIcon.after(searchForm);
        }
    });
});

