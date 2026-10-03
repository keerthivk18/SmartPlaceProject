const searchInput = document.querySelector('input[name="q"]');
const searchForm = document.querySelector('.search-box');
const searchWrapper = document.querySelector('.search-input-wrapper');
const suggestionsBox = document.querySelector('.search-suggestions');

if (searchInput && searchForm && searchWrapper && suggestionsBox) {

    /* Search form layout */
    searchForm.style.display = 'flex';
    searchForm.style.alignItems = 'center';
    searchForm.style.justifyContent = 'center';
    searchForm.style.gap = '8px';
    searchForm.style.position = 'relative';

    /* Search input area */
    searchWrapper.style.position = 'relative';
    searchWrapper.style.width = '390px';
    searchWrapper.style.flexShrink = '0';

    searchInput.style.width = '100%';
    searchInput.style.height = '44px';
    searchInput.style.boxSizing = 'border-box';

    /* Dropdown */
    suggestionsBox.style.position = 'absolute';
    suggestionsBox.style.top = '50px';
    suggestionsBox.style.left = '0';
    suggestionsBox.style.width = '100%';
    suggestionsBox.style.backgroundColor = '#ffffff';
    suggestionsBox.style.border = '1px solid #d8dee6';
    suggestionsBox.style.borderRadius = '10px';
    suggestionsBox.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.14)';
    suggestionsBox.style.overflow = 'hidden';
    suggestionsBox.style.zIndex = '99999';
    suggestionsBox.style.display = 'none';

    searchInput.addEventListener('input', async function () {

        const query = this.value.trim();

        suggestionsBox.innerHTML = '';

        if (!query) {
            suggestionsBox.style.display = 'none';
            return;
        }

        try {
            const response = await fetch(
                `/search-suggestions/?q=${encodeURIComponent(query)}`
            );

            if (!response.ok) {
                throw new Error('Suggestion request failed');
            }

            const places = await response.json();

            if (places.length === 0) {
                suggestionsBox.style.display = 'none';
                return;
            }

            places.forEach(function (place) {

                const link = document.createElement('a');

                link.href = `/place/${place.id}/`;

                link.style.display = 'block';
                link.style.width = '100%';
                link.style.boxSizing = 'border-box';
                link.style.padding = '12px 15px';
                link.style.textDecoration = 'none';
                link.style.textAlign = 'left';
                link.style.color = '#2c3e50';
                link.style.backgroundColor = '#ffffff';
                link.style.borderBottom = '1px solid #eeeeee';

                link.addEventListener('mouseenter', function () {
                    link.style.backgroundColor = '#f4f7fa';
                });

                link.addEventListener('mouseleave', function () {
                    link.style.backgroundColor = '#ffffff';
                });

                const name = document.createElement('div');

                name.textContent = place.name;
                name.style.fontSize = '15px';
                name.style.fontWeight = '600';

                const city = document.createElement('div');

                city.textContent = place.city;
                city.style.marginTop = '4px';
                city.style.fontSize = '13px';
                city.style.color = '#777777';

                link.appendChild(name);
                link.appendChild(city);

                suggestionsBox.appendChild(link);
            });

            suggestionsBox.style.display = 'block';

        } catch (error) {

            console.error('Autocomplete error:', error);
            suggestionsBox.style.display = 'none';

        }
    });


    document.addEventListener('click', function (event) {

        if (!searchForm.contains(event.target)) {
            suggestionsBox.style.display = 'none';
        }

    });
}