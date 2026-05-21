pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        PYTHON_EXE = "C:\\\\Users\\\\hamza\\\\.pyenv\\\\pyenv-win\\\\versions\\\\3.10.0\\\\python.exe"
        VENV_DIR = ".venv"
        RUN_ID = ""
    }

    stages {
        stage("Checkout") {
            steps {
                checkout scm
            }
        }

        stage("Setup") {
            steps {
                powershell "python -m venv ${env.VENV_DIR}"
                powershell ".\\${env.VENV_DIR}\\Scripts\\Activate.ps1; python -m pip install --upgrade pip"
                powershell ".\\${env.VENV_DIR}\\Scripts\\Activate.ps1; pip install -r requirements.txt"
            }
        }

        stage("Tests") {
            steps {
                powershell "if ((Test-Path tests) -or (Test-Path pytest.ini) -or (Test-Path pyproject.toml)) { .\\${env.VENV_DIR}\\Scripts\\Activate.ps1; pytest -q } else { Write-Host 'No tests found, skipping.' }"
            }
        }

        stage("Train") {
            steps {
                powershell ".\\${env.VENV_DIR}\\Scripts\\Activate.ps1; python -m madewithml.train --experiment-name mlops-project --num-epochs 1 --results-fp results.json"
                script {
                    env.RUN_ID = powershell(
                        script: ".\\${env.VENV_DIR}\\Scripts\\Activate.ps1; python - <<'PY'\nimport json\nwith open('results.json') as fp:\n    print(json.load(fp)['run_id'])\nPY",
                        returnStdout: true
                    ).trim()
                }
                echo "Using run_id: ${env.RUN_ID}"
            }
        }

        stage("Evaluate") {
            steps {
                powershell ".\\${env.VENV_DIR}\\Scripts\\Activate.ps1; python -m madewithml.evaluate --run-id ${env.RUN_ID} --dataset-loc datasets/holdout.csv --results-fp eval-results.json"
            }
        }

        stage("Serve") {
            steps {
                powershell "${proc = Start-Process -FilePath 'python' -ArgumentList '-m madewithml.serve --run_id ${env.RUN_ID} --host 127.0.0.1 --port 8000' -PassThru; Start-Sleep -Seconds 3; Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing | Select-Object -ExpandProperty Content; Stop-Process -Id $proc.Id -Force}"
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: "**/results.json", allowEmptyArchive: true
            archiveArtifacts artifacts: "**/eval-results.json", allowEmptyArchive: true
            junit allowEmptyResults: true, testResults: "**/test-results.xml"
        }
    }
}
