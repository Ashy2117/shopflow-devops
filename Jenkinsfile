pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  stages {
    stage('Test') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -r requirements-dev.txt
          pip install -r services/catalog/requirements.txt
          pip install -r services/orders/requirements.txt
          pytest -q
        '''
      }
    }
    stage('Build images') {
      steps {
        sh 'docker build -t shopflow/catalog-api:0.1.0 services/catalog'
        sh 'docker build -t shopflow/orders-api:0.1.0 services/orders'
      }
    }
    stage('Scan if Trivy installed') {
      steps {
        sh '''
          if command -v trivy >/dev/null 2>&1; then
            trivy image --severity HIGH,CRITICAL --exit-code 1 shopflow/catalog-api:0.1.0
            trivy image --severity HIGH,CRITICAL --exit-code 1 shopflow/orders-api:0.1.0
          else
            echo "Trivy missing on agent; scan skipped."
          fi
        '''
      }
    }
  }
}
