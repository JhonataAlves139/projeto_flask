function MostrarSenha() {
    const senhaInput = document.getElementById('senha');
    const btnSenha = document.getElementById('btn-senha');
    
    if (senhaInput.type === "password") {
        senhaInput.type = "text";
        btnSenha.classList.remove("bi-eye-fill");
        btnSenha.classList.add("bi-eye-slash-fill");
    } else {
        senhaInput.type = "password";
        btnSenha.classList.remove("bi-eye-slash-fill");
        btnSenha.classList.add("bi-eye-fill");
    }
}

// Adicionar efeito de ripple nos botões
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('button');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const x = e.clientX - e.target.offsetLeft;
            const y = e.clientY - e.target.offsetTop;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Adicionar efeitos de foco nos inputs
    const inputs = document.querySelectorAll('input');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focus');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focus');
        });
    });
});
