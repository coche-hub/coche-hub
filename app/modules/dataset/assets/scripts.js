var currentId = 0;
        var amount_authors = 0;

        function show_upload_dataset() {
            document.getElementById("upload_dataset").style.display = "block";
        }

        function generateIncrementalId() {
            return currentId++;
        }

        function addField(newAuthor, name, text, className = 'col-lg-6 col-12 mb-3') {
            let fieldWrapper = document.createElement('div');
            fieldWrapper.className = className;

            let label = document.createElement('label');
            label.className = 'form-label';
            label.for = name;
            label.textContent = text;

            let field = document.createElement('input');
            field.name = name;
            field.className = 'form-control';

            fieldWrapper.appendChild(label);
            fieldWrapper.appendChild(field);
            newAuthor.appendChild(fieldWrapper);
        }

        function addRemoveButton(newAuthor) {
            let buttonWrapper = document.createElement('div');
            buttonWrapper.className = 'col-12 mb-2';

            let button = document.createElement('button');
            button.textContent = 'Remove author';
            button.className = 'btn btn-danger btn-sm';
            button.type = 'button';
            button.addEventListener('click', function (event) {
                event.preventDefault();
                newAuthor.remove();
            });

            buttonWrapper.appendChild(button);
            newAuthor.appendChild(buttonWrapper);
        }

        function createAuthorBlock(idx, suffix) {
            let newAuthor = document.createElement('div');
            newAuthor.className = 'author row';
            newAuthor.style.cssText = "border:2px dotted #ccc;border-radius:10px;padding:10px;margin:10px 0; background-color: white";

            addField(newAuthor, `${suffix}authors-${idx}-name`, 'Name *');
            addField(newAuthor, `${suffix}authors-${idx}-affiliation`, 'Affiliation');
            addField(newAuthor, `${suffix}authors-${idx}-orcid`, 'ORCID');
            addRemoveButton(newAuthor);

            return newAuthor;
        }

        function check_title_and_description() {
            let titleInput = document.querySelector('input[name="title"]');
            let descriptionTextarea = document.querySelector('textarea[name="desc"]');

            titleInput.classList.remove("error");
            descriptionTextarea.classList.remove("error");
            clean_upload_errors();

            let titleLength = titleInput.value.trim().length;
            let descriptionLength = descriptionTextarea.value.trim().length;

            if (titleLength < 3) {
                write_upload_error("title must be of minimum length 3");
                titleInput.classList.add("error");
            }

            if (descriptionLength < 3) {
                write_upload_error("description must be of minimum length 3");
                descriptionTextarea.classList.add("error");
            }

            return (titleLength >= 3 && descriptionLength >= 3);
        }


        document.getElementById('add_author').addEventListener('click', function () {
            let authors = document.getElementById('authors');
            let newAuthor = createAuthorBlock(amount_authors++, "");
            authors.appendChild(newAuthor);
        });


        document.addEventListener('click', function (event) {
            if (event.target && event.target.classList.contains('add_author_to_uvl')) {

                let authorsButtonId = event.target.id;
                let authorsId = authorsButtonId.replace("_button", "");
                let authors = document.getElementById(authorsId);
                let id = authorsId.replace("_form_authors", "")
                let newAuthor = createAuthorBlock(amount_authors, `feature_models-${id}-`);
                authors.appendChild(newAuthor);

            }
        });

        function show_loading() {
            document.getElementById("upload_button").style.display = "none";
            document.getElementById("loading").style.display = "block";
        }

        function hide_loading() {
            document.getElementById("upload_button").style.display = "block";
            document.getElementById("loading").style.display = "none";
        }

        function clean_upload_errors() {
            let upload_error = document.getElementById("upload_error");
            upload_error.innerHTML = "";
            upload_error.style.display = 'none';
        }

        function write_upload_error(error_message) {
            let upload_error = document.getElementById("upload_error");
            let alert = document.createElement('p');
            alert.style.margin = '0';
            alert.style.padding = '0';
            alert.textContent = 'Upload error: ' + error_message;
            upload_error.appendChild(alert);
            upload_error.style.display = 'block';
        }

        window.onload = function () {

            test_zenodo_connection();

            document.getElementById('upload_button').addEventListener('click', function () {

                clean_upload_errors();
                show_loading();

                // check title and description
                let check = check_title_and_description();

                if (check) {
                    // process data form
                    const formData = {};

                    ["basic_info_form", "uploaded_models_form"].forEach((formId) => {
                        const form = document.getElementById(formId);
                        const inputs = form.querySelectorAll('input, select, textarea');
                        inputs.forEach(input => {
                            if (input.name) {
                                formData[input.name] = formData[input.name] || [];
                                formData[input.name].push(input.value);
                            }
                        });
                    });

                    let formDataJson = JSON.stringify(formData);
                    console.log(formDataJson);

                    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
                    const formUploadData = new FormData();
                    formUploadData.append('csrf_token', csrfToken);

                    for (let key in formData) {
                        if (formData.hasOwnProperty(key)) {
                            formUploadData.set(key, formData[key]);
                        }
                    }

                    let checked_orcid = true;
                    if (Array.isArray(formData.author_orcid)) {
                        for (let orcid of formData.author_orcid) {
                            orcid = orcid.trim();
                            if (orcid !== '' && !isValidOrcid(orcid)) {
                                hide_loading();
                                write_upload_error("ORCID value does not conform to valid format: " + orcid);
                                checked_orcid = false;
                                break;
                            }
                        }
                    }


                    let checked_name = true;
                    if (Array.isArray(formData.author_name)) {
                        for (let name of formData.author_name) {
                            name = name.trim();
                            if (name === '') {
                                hide_loading();
                                write_upload_error("The author's name cannot be empty");
                                checked_name = false;
                                break;
                            }
                        }
                    }


                    if (checked_orcid && checked_name) {
                        fetch('/dataset/upload', {
                            method: 'POST',
                            body: formUploadData
                        })
                            .then(response => {
                                if (response.ok) {
                                    console.log('Dataset sent successfully');
                                    response.json().then(data => {
                                        console.log(data.message);
                                        window.location.href = "/dataset/list";
                                    });
                                } else {
                                    response.json().then(data => {
                                        console.error('Error: ' + data.message);
                                        hide_loading();

                                        write_upload_error(data.message);

                                    });
                                }
                            })
                            .catch(error => {
                                console.error('Error in POST request:', error);
                            });
                    }


                } else {
                    hide_loading();
                }


            });
        };


        function isValidOrcid(orcid) {
            let orcidRegex = /^\d{4}-\d{4}-\d{4}-\d{4}$/;
            return orcidRegex.test(orcid);
        }

        document.addEventListener('DOMContentLoaded', function () {
            // Initialize Dropzone
            Dropzone.autoDiscover = false;

            const dropzoneElement = document.getElementById('myDropzone');
            if (!dropzoneElement) {
                console.error('Dropzone element not found');
                return;
            }

            const myDropzone = new Dropzone("#myDropzone", {
                url: "/dataset/file/upload",
                autoProcessQueue: false,
                uploadMultiple: true,
                parallelUploads: 10,
                maxFilesize: 100,
                acceptedFiles: '.csv',  // Solo CSV
                addRemoveLinks: true,
                init: function () {
                    var submitButton = document.getElementById("submit_btn");
                    var myDropzone = this;

                    submitButton.addEventListener("click", function (e) {
                        e.preventDefault();
                        e.stopPropagation();

                        if (myDropzone.getQueuedFiles().length > 0) {
                            myDropzone.processQueue();
                        } else {
                            // No files to upload, submit form directly
                            submitFormWithoutFiles();
                        }
                    });

                    this.on("addedfile", function (file) {
                        console.log("File added: ", file);
                    });

                    this.on("complete", function (file) {
                        if (this.getUploadingFiles().length === 0 && this.getQueuedFiles().length === 0) {
                            submitFormWithoutFiles();
                        }
                    });

                    this.on("error", function (file, message) {
                        console.error("Upload error: ", message);
                        write_upload_error(message);
                    });
                }
            });

            function submitFormWithoutFiles() {
                show_loading();

                // Get form data
                const form = document.getElementById('upload_form');
                const formData = new FormData(form);

                // Remove feature_models fields (legacy from UVL)
                const keysToDelete = [];
                for (let key of formData.keys()) {
                    if (key.startsWith('feature_models-') || key.startsWith('authors-')) {
                        keysToDelete.push(key);
                    }
                }
                keysToDelete.forEach(key => formData.delete(key));

                // Add files from temp folder
                const uploadedFiles = myDropzone.getAcceptedFiles();
                uploadedFiles.forEach((file, index) => {
                    formData.append(`files[${index}]`, file.upload.filename || file.name);
                });

                // Add authors
                const authorForms = document.querySelectorAll('.author-form');
                authorForms.forEach((authorForm, index) => {
                    const name = authorForm.querySelector('input[name*="name"]');
                    const affiliation = authorForm.querySelector('input[name*="affiliation"]');
                    const orcid = authorForm.querySelector('input[name*="orcid"]');
                    
                    if (name && name.value.trim()) {
                        formData.append(`authors-${index}-name`, name.value);
                        formData.append(`authors-${index}-affiliation`, affiliation ? affiliation.value : '');
                        formData.append(`authors-${index}-orcid`, orcid ? orcid.value : '');
                    }
                });

                console.log('Submitting form data:', Object.fromEntries(formData));

                fetch('/dataset/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        console.log('Dataset sent successfully');
                        response.json().then(data => {
                            console.log(data.message);
                            window.location.href = "/dataset/list";
                        });
                    } else {
                        response.json().then(data => {
                            console.error('Error response:', data);
                            hide_loading();
                            
                            // Better error handling
                            let errorMessage = 'Unknown error';
                            if (typeof data.message === 'string') {
                                errorMessage = data.message;
                            } else if (typeof data.message === 'object') {
                                // Convert object errors to readable format
                                errorMessage = JSON.stringify(data.message, null, 2);
                                
                                // Try to extract field-specific errors
                                const errors = [];
                                for (let field in data.message) {
                                    if (Array.isArray(data.message[field])) {
                                        errors.push(`${field}: ${data.message[field].join(', ')}`);
                                    }
                                }
                                if (errors.length > 0) {
                                    errorMessage = errors.join('\n');
                                }
                            } else if (data.error) {
                                errorMessage = data.error;
                            }
                            
                            write_upload_error(errorMessage);
                        }).catch(err => {
                            console.error('Error parsing response:', err);
                            hide_loading();
                            write_upload_error('Error parsing server response');
                        });
                    }
                })
                .catch(error => {
                    console.error('Error in POST request:', error);
                    hide_loading();
                    write_upload_error('Network error: ' + error.message);
                });
            }

            function show_loading() {
                document.getElementById('loading').style.display = 'block';
            }

            function hide_loading() {
                document.getElementById('loading').style.display = 'none';
            }

            function write_upload_error(message) {
                const errorDiv = document.getElementById('upload_error');
                if (errorDiv) {
                    errorDiv.innerHTML = `<div class="alert alert-danger">${message}</div>`;
                    errorDiv.style.display = 'block';
                }
            }
        });