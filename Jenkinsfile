pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    CATALOG_IMAGE = 'shopflow/catalog-api:0.1.0'
    ORDERS_IMAGE = 'shopflow/orders-api:0.1.0'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Test') {
      steps {
        sh '''
          python3 -m venv .ci-venv
          . .ci-venv/bin/activate
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
          pip install -r services/catalog/requirements.txt
          pip install -r services/orders/requirements.txt
          python -m pytest -v
        '''
      }
    }

    stage('Build images') {
      steps {
        sh 'docker build -t "$CATALOG_IMAGE" services/catalog'
        sh 'docker build -t "$ORDERS_IMAGE" services/orders'
      }
    }

    stage('Security scan') {
      steps {
        sh '''
          command -v trivy
          trivy image --severity HIGH,CRITICAL --exit-code 1 "$CATALOG_IMAGE"
          trivy image --severity HIGH,CRITICAL --exit-code 1 "$ORDERS_IMAGE"
        '''
      }
    }
  }

  post {
    always {
      echo 'ShopFlow CI pipeline finished. Review stage results above.'
    }
  }
}
