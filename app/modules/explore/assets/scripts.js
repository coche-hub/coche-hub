document.addEventListener('DOMContentLoaded', () => {
    send_query();
});

function send_query() {

    console.log("send query...")

    document.getElementById('results').innerHTML = '';
    document.getElementById("results_not_found").style.display = "none";
    console.log("hide not found icon");

    const filters = document.querySelectorAll('#filters input, #filters select, #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {
            const csrfToken = document.getElementById('csrf_token').value;

            const searchCriteria = {
                csrf_token: csrfToken,
                title: document.querySelector('#title').value,
                author: document.querySelector('#author').value,
                tags: document.querySelector('#tags').value,
                community: document.querySelector('#community').value,
                publication_type: document.querySelector('#publication_type').value,
                date_from: document.querySelector('#date_from').value,
                date_to: document.querySelector('#date_to').value,
                engine_size_min: document.querySelector('#engine_size_min').value,
                engine_size_max: document.querySelector('#engine_size_max').value,
                consumption_min: document.querySelector('#consumption_min').value,
                consumption_max: document.querySelector('#consumption_max').value,
                sorting: document.querySelector('[name="sorting"]:checked').value,
            };

            console.log(document.querySelector('#publication_type').value);

            fetch('/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchCriteria),
            })
                .then(response => response.json())
                .then(data => {

                    console.log(data);
                    document.getElementById('results').innerHTML = '';

                    // results counter
                    const resultCount = data.length;
                    const resultText = resultCount === 1 ? 'dataset' : 'datasets';
                    document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

                    if (resultCount === 0) {
                        console.log("show not found icon");
                        document.getElementById("results_not_found").style.display = "block";
                    } else {
                        document.getElementById("results_not_found").style.display = "none";
                    }


                    data.forEach(dataset => {
                        let card = document.createElement('div');
                        card.className = 'col-12';
                        card.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex align-items-center justify-content-between">
                                        <h3><a href="${dataset.url}">${dataset.title}</a></h3>
                                        <div>
                                            <span class="badge bg-primary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
                                        </div>
                                    </div>
                                    <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Description
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            <p class="card-text">${dataset.description}</p>
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Authors
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.authors.map(author => `
                                                <p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>
                                            `).join('')}
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Tags
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('')}
                                        </div>

                                    </div>

                                    <div class="row">

                                        <div class="col-md-4 col-12">

                                        </div>
                                        <div class="col-md-8 col-12">
                                            <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                View dataset
                                            </a>
                                            <a href="/dataset/download/${dataset.id}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                Download (${dataset.total_size_in_human_format})
                                            </a>
                                        </div>


                                    </div>

                                </div>
                            </div>
                        `;

                        document.getElementById('results').appendChild(card);
                    });
                });
        });
    });
}

function formatDate(dateString) {
    const options = {day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: 'numeric'};
    const date = new Date(dateString);
    return date.toLocaleString('en-US', options);
}

function set_tag_as_query(tagName) {
    const queryInput = document.getElementById('query');
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_publication_type_as_query(publicationType) {
    const publicationTypeSelect = document.getElementById('publication_type');
    for (let i = 0; i < publicationTypeSelect.options.length; i++) {
        if (publicationTypeSelect.options[i].text === publicationType.trim()) {
            // Set the value of the select to the value of the matching option
            publicationTypeSelect.value = publicationTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {

    // Reset all search fields
    let titleInput = document.querySelector('#title');
    titleInput.value = "";

    let authorInput = document.querySelector('#author');
    authorInput.value = "";

    let tagsInput = document.querySelector('#tags');
    tagsInput.value = "";

    let communityInput = document.querySelector('#community');
    communityInput.value = "";

    // Reset the publication type to its default value
    let publicationTypeSelect = document.querySelector('#publication_type');
    publicationTypeSelect.value = "";

    // Reset date fields
    let dateFromInput = document.querySelector('#date_from');
    dateFromInput.value = "";

    let dateToInput = document.querySelector('#date_to');
    dateToInput.value = "";

    // Reset engine size fields
    let engineSizeMinInput = document.querySelector('#engine_size_min');
    engineSizeMinInput.value = "";

    let engineSizeMaxInput = document.querySelector('#engine_size_max');
    engineSizeMaxInput.value = "";

   // Reset consumption fields
    let consumptionMinInput = document.querySelector('#consumption_min');
    consumptionMinInput.value = "";

    let consumptionMaxInput = document.querySelector('#consumption_max');
    consumptionMaxInput.value = ""; 

    // Reset the sorting option
    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value == "newest";
    });

    // Perform a new search with the reset filters
    titleInput.dispatchEvent(new Event('input', {bubbles: true}));
}

document.addEventListener('DOMContentLoaded', () => {

    let urlParams = new URLSearchParams(window.location.search);
    let titleParam = urlParams.get('title');
    let authorParam = urlParams.get('author');
    let tagsParam = urlParams.get('tags');
    let communityParam = urlParams.get('community');
    let publicationTypeParam = urlParams.get('publication_type');
    let dateFromParam = urlParams.get('date_from');
    let dateToParam = urlParams.get('date_to');
    let engineSizeMinParam = urlParams.get('engine_size_min');
    let engineSizeMaxParam = urlParams.get('engine_size_max');
    let consumptionMinParam = urlParams.get('consumption_min');
    let consumptionMaxParam = urlParams.get('consumption_max');

    if (titleParam && titleParam.trim() !== '') {
        const titleInput = document.getElementById('title');
        titleInput.value = titleParam;
    }

    if (authorParam && authorParam.trim() !== '') {
        const authorInput = document.getElementById('author');
        authorInput.value = authorParam;
    }

    if (tagsParam && tagsParam.trim() !== '') {
        const tagsInput = document.getElementById('tags');
        tagsInput.value = tagsParam;
    }

    if (communityParam && communityParam.trim() !== '') {
        const communitySelect = document.getElementById('community');
        communitySelect.value = communityParam;
    }

    if (publicationTypeParam && publicationTypeParam.trim() !== '') {
        const publicationTypeSelect = document.getElementById('publication_type');
        publicationTypeSelect.value = publicationTypeParam;
    }

    if (dateFromParam && dateFromParam.trim() !== '') {
        const dateFromInput = document.getElementById('date_from');
        dateFromInput.value = dateFromParam;
    }

    if (dateToParam && dateToParam.trim() !== '') {
        const dateToInput = document.getElementById('date_to');
        dateToInput.value = dateToParam;
    }

    if (engineSizeMinParam && engineSizeMinParam.trim() !== '') {
        const engineSizeMinInput = document.getElementById('engine_size_min');
        engineSizeMinInput.value = engineSizeMinParam;
    }

    if (engineSizeMaxParam && engineSizeMaxParam.trim() !== '') {
        const engineSizeMaxInput = document.getElementById('engine_size_max');
        engineSizeMaxInput.value = engineSizeMaxParam;
    }

    if (consumptionMinParam && consumptionMinParam.trim() !== '') {
        const consumptionMinInput = document.getElementById('consumption_min');
        consumptionMinInput.value = consumptionMinParam;
    }

    if (consumptionMaxParam && consumptionMaxParam.trim() !== '') {
        const consumptionMaxInput = document.getElementById('consumption_max');
        consumptionMaxInput.value = consumptionMaxParam;
    }

    const titleInput = document.getElementById('title');
    titleInput.dispatchEvent(new Event('input', {bubbles: true}));
});