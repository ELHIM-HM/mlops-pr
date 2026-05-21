pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
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
                sh "python3 -m venv ${VENV_DIR}"
                sh ". ${VENV_DIR}/bin/activate; python -m pip install --upgrade pip"
                sh ". ${VENV_DIR}/bin/activate; pip install -r requirements.txt"
            }
        }

        stage("Tests") {
            steps {
                sh "if [ -d tests ] || [ -f pytest.ini ] || [ -f pyproject.toml ]; then . ${VENV_DIR}/bin/activate; pytest -q; else echo 'No tests found, skipping.'; fi"
            }
        }

        stage("Train") {
            steps {
                sh ". ${VENV_DIR}/bin/activate; python -m madewithml.train --experiment-name mlops-project --num-epochs 1 --results-fp results.json"
                script {
                    env.RUN_ID = sh(
                        script: ". ${VENV_DIR}/bin/activate; python - <<'PY'\nimport json\nwith open('results.json') as fp:\n    print(json.load(fp)['run_id'])\nPY",
                        returnStdout: true
                    ).trim()
                }
                echo "Using run_id: ${env.RUN_ID}"
            }
        }

        stage("Evaluate") {
            steps {
                sh ". ${VENV_DIR}/bin/activate; python -m madewithml.evaluate --run-id ${RUN_ID} --dataset-loc datasets/holdout.csv --results-fp eval-results.json"
            }
        }

        stage("Serve") {
            steps {
                sh ". ${VENV_DIR}/bin/activate; python -m madewithml.serve --run_id ${RUN_ID} --host 127.0.0.1 --port 8000 >/tmp/serve.log 2>&1 &"
                sh "sleep 3"
                sh ". ${VENV_DIR}/bin/activate; python - <<'PY'\nimport json\nimport urllib.request\nurl = 'http://127.0.0.1:8000/'\nwith urllib.request.urlopen(url) as resp:\n    print(resp.read().decode('utf-8'))\nPY"
                sh "pkill -f 'madewithml.serve' || true"
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
