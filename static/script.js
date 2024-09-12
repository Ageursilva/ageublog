document.addEventListener('DOMContentLoaded', () => {
    const searchIcon = document.querySelector('.search-icon');

    searchIcon.addEventListener('click', () => {

        if (!document.querySelector('.search-form')) {
   
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
            
        
            searchForm.appendChild(searchInput);
            searchForm.appendChild(searchButton);

            searchIcon.after(searchForm);
        }
    });
});

document.getElementById('roll-dice-trigger').addEventListener('click', function() {
 
    document.getElementById('dice-container').classList.remove('hidden');
  
    
    let dice = document.getElementById('dice-result');
    dice.textContent = "🎲";  
    dice.classList.add('roll-animation'); 
  
  
    setTimeout(function() {
        dice.textContent = "Você tirou 20!";
        dice.classList.remove('roll-animation');
  
        
        setTimeout(function() {
            window.location.href = homeUrl; 
        }, 2000);
    }, 2000);
  });
  
