document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.user-search-input').forEach(input => {
        const wrapper = input.closest('.user-search-wrapper');
        const suggestionBox = wrapper.querySelector('.user-suggestions');
        const hiddenInput = wrapper.querySelector('input[type="hidden"]');
        const searchUrl = suggestionBox.dataset.searchUrl;

        input.addEventListener('input', async () => {
            const query = input.value.trim();
            if (query.length < 2) {
                suggestionBox.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
                const users = await response.json();

                suggestionBox.innerHTML = '';
                users.forEach(user => {
                    const li = document.createElement('li');
                    li.textContent = `${user.name}`;
                    li.dataset.userId = user.id;
                    li.classList.add('suggestion-item');
                    li.addEventListener('click', () => {
                        input.value = `${user.name}`;
                        hiddenInput.value = user.id;
                        suggestionBox.style.display = 'none';
                    });
                    suggestionBox.appendChild(li);
                });

                suggestionBox.style.display = users.length ? 'block' : 'none';
            } catch (e) {
                console.error('AJAX error', e);
            }
        });

        input.addEventListener('blur', () => {
            setTimeout(() => suggestionBox.style.display = 'none', 200);
        });
    });
});
