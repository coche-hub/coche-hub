<div style="text-align: center;">
  <img src="app/static/img/logos/car.png" alt="Logo">
</div>

# Cochehub.io

Repository of car models in CSV format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab


## Development

Before running the server for local development, you'll need to get an instance of Mailhog running through docker.
Of course, this means you will need to have Docker and docker compose installed even for local development.
For guidance on how, see the original CocheHub documentation.
Run:
```
docker compose --env-file .env -f ./docker/docker-compose.local.yml up
```

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

