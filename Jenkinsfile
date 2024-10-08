pipeline {
    agent { label 'small' }
    environment {
      imagename_dev = "ghcr.io/pilotdataplatform/auth"
      imagename_staging = "ghcr.io/pilotdataplatform/auth"
      commit = sh(returnStdout: true, script: 'git describe --always').trim()
      registryCredential = 'pilot-ghcr'
      dockerImage = ''
    }

    stages {

    stage('Git clone for dev') {
        when {branch "develop"}
        steps{
          script {
          git branch: "develop",
              url: 'https://github.com/PilotDataPlatform/auth'
            }
        }
    }

    stage('DEV unit test') {
        when { branch 'develop' }
        steps {
            withCredentials([
                string(credentialsId:'VAULT_TOKEN', variable: 'VAULT_TOKEN'),
                string(credentialsId:'VAULT_URL', variable: 'VAULT_URL'),
                file(credentialsId:'VAULT_CRT', variable: 'VAULT_CRT')
            ]) {
                sh """
                pip install --user poetry==1.1.12
                ${HOME}/.local/bin/poetry config virtualenvs.in-project true
                ${HOME}/.local/bin/poetry install --no-root --no-interaction
                ${HOME}/.local/bin/poetry run pytest --verbose -c tests/pytest.ini
                """
            }
        }
    }

    stage('DEV Build and push image') {
      when {branch "develop"}
      steps{
        script {
          docker.withRegistry('https://ghcr.io', registryCredential) {
              customImage = docker.build("$imagename_dev:$commit-CAC", "--add-host git.indocresearch.org:10.4.3.151 .")
              customImage.push()
          }
        }
      }
    }

    stage('DEV Remove image') {
      when {branch "develop"}
      steps{
        sh "docker rmi $imagename_dev:$commit-CAC"
      }
    }

    stage('DEV Deploy') {
      when {branch "develop"}
      steps{
        build(job: "/VRE-IaC/UpdateAppVersion", parameters: [
          [$class: 'StringParameterValue', name: 'TF_TARGET_ENV', value: 'dev' ],
          [$class: 'StringParameterValue', name: 'TARGET_RELEASE', value: 'auth' ],
          [$class: 'StringParameterValue', name: 'NEW_APP_VERSION', value: "$commit-CAC" ]
      ])
      }
    }

    stage('Git clone staging') {
        when {branch "main"}
        steps{
          script {
          git branch: "main",
              url: 'https://github.com/PilotDataPlatform/auth'
            }
        }
    }

    stage('STAGING Building and push image') {
      when {branch "main"}
      steps{
        script {
          docker.withRegistry('https://ghcr.io', registryCredential) {
              customImage = docker.build("$imagename_staging:$commit", "--add-host git.indocresearch.org:10.4.3.151 .")
              customImage.push()
          }
        }
      }
    }

    stage('STAGING Remove image') {
      when {branch "main"}
      steps{
        sh "docker rmi $imagename_staging:$commit"
      }
    }

    stage('STAGING Deploy') {
      when {branch "main"}
      steps{
      build(job: "/VRE-IaC/Staging-UpdateAppVersion", parameters: [
        [$class: 'StringParameterValue', name: 'TF_TARGET_ENV', value: 'staging' ],
        [$class: 'StringParameterValue', name: 'TARGET_RELEASE', value: 'auth' ],
        [$class: 'StringParameterValue', name: 'NEW_APP_VERSION', value: "$commit" ]
      ])
      }
    }
  }
  post {
    failure {
        slackSend color: '#FF0000', message: "Build Failed! - ${env.JOB_NAME} commit_hash:$commit  (<${env.BUILD_URL}|Open>)", channel: 'jenkins-dev-staging-monitor'
    }
  }

}
