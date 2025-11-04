<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

## Development

After running the steps for a local installation required for the documentation, and within the venv, run:

```bash
pre-commit install
pre-commit install -t pre-merge-commit
pre-commit install -t commit-msg
```

In order for the tests to run when merging, `--no-ff` must be used.

```
git merge --no-ff <branch>
```

