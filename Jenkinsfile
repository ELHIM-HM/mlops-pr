pipeline {
    // This tells Jenkins to pull the official Python 3.10 image and run all steps inside it!
    agent {
        docker {
            image 'python:3.10.0-slim'
        }
    }

    options {
        timestamps()
    }

    environment {
        // Standard Linux paths now!
        VENV_DIR = ".venv"
        VENV_PY = ".venv/bin/python" 
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
                sh "python -m venv ${env.VENV_DIR}"
                sh "${env.VENV_PY} -m pip install --upgrade pip"
                sh "${env.VENV_PY} -m pip install -r requirements.txt"
            }
        }

        stage("Tests") {
            steps {
                sh '''
                    if [ -d "tests" ] || [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
                        ${VENV_PY} -m pytest -q
                    else
                        echo "No tests found, skipping."
                    fi
                '''
            }
        }

        stage("Train") {
            steps {
                sh "${env.VENV_PY} -m madewithml.train --experiment-name mlops-project --num-epochs 1 --results-fp results.json"

                // Read run_id from MLflow after training
                sh "${env.VENV_PY} -c \"from madewithml.config import MLFLOW_TRACKING_URI, mlflow; mlflow.set_tracking_uri(MLFLOW_TRACKING_URI); runs = mlflow.search_runs(experiment_names=['mlops-project'], order_by=['metrics.val_loss ASC']); print(runs.iloc[0].run_id)\" > run_id.txt"

                script {
                    env.RUN_ID = readFile('run_id.txt').trim()
                }
                echo "Successfully captured run_id: ${env.RUN_ID}"
            }
        }

        stage("Evaluate") {
            steps {
                sh "${env.VENV_PY} -m madewithml.evaluate --run-id ${env.RUN_ID} --dataset-loc datasets/holdout.csv --results-fp eval-results.json"
            }
        }

        stage("Serve") {
            steps {
                sh '''
                    # Start the server in the background (&)
                    ${VENV_PY} -m madewithml.serve --run_id ${RUN_ID} --host 127.0.0.1 --port 8000 &
                    SERVER_PID=$!
                    
                    # Wait for it to boot up
                    sleep 5
                    
                    # Use Python's built-in urllib to test the endpoint (replaces Invoke-WebRequest)
                    ${VENV_PY} -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/').read().decode('utf-8'))"
                    
                    # Kill the background process
                    kill $SERVER_PID
                '''
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