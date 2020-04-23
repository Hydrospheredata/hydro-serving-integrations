def repository = 'hydro-serving-integrations'

def buildAndPublishReleaseFunction = {
    withCredentials([
        string(credentialsId: 'HydrosphereDevEndpoint', variable: 'HYDROSPHERE_ENDPOINT'),
        string(credentialsId: 'HydroIntegrationsAWSRegion', variable: 'AWS_DEFAULT_REGION'),
        string(credentialsId: 'HydroIntegrationsS3DataCaptureBucket', variable: 'S3_DATA_CAPTURE_BUCKET'),
        string(credentialsId: 'HydroIntegrationsS3DataCapturePrefix', variable: 'S3_DATA_CAPTURE_PREFIX'),
        string(credentialsId: 'HydroIntegrationsS3DataTrainingBucket', variable: 'S3_DATA_TRAINING_BUCKET'),
        string(credentialsId: 'HydroIntegrationsS3DataTrainingPrefix', variable: 'S3_DATA_TRAINING_PREFIX'),
        [
            $class: 'AmazonWebServicesCredentialsBinding',
            credentialsId: 'aws-hydrosphere-jenkins-credentials',
            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
        ],
    ]) {
        configFileProvider([configFile(fileId: 'PYPIDeployConfiguration', targetLocation: '.pypirc', variable: 'PYPI_SETTINGS')]) {
            sh """#!/bin/bash
            set -ex

            # prepare environment
            pyenv install --skip-existing 3.6.10
            pyenv install --skip-existing 3.7.7
            pyenv install --skip-existing 3.8.2
            eval "\$(pyenv init -)"
            pyenv shell 3.6.10 3.7.7 3.8.2
            
            python -m venv venv
            source venv/bin/activate
            pip install wheel~=0.34.2
            pip install tox~=3.14.5
            pip install aws-sam-cli~=0.47.0
            pip install twine~=3.1.1
            pip install awscli~=1.18.44

            # run tests for lambda distribution
            # and for hydro-integrations sdk
            tox

            # build lambda distribution artifacts
            cd scripts/aws/traffic_shadowing
            ./sam-build.sh
            ./sam-package.sh
            
            # publish lambda distribution artifacts
            ./cf-build-upload.sh
            cd ../../../
            
            # build hydro-integrations sdk
            pip install -r requirements.txt
            python setup.py bdist_wheel

            # publish hydro-integrations sdk package
            python -m twine upload --config-file ${env.WORKSPACE}/.pypirc -r pypi ${env.WORKSPACE}/dist/*
            deactivate
            """
        }
    }
}

def buildFunction = {
    withCredentials([
        string(credentialsId: 'HydrosphereDevEndpoint', variable: 'HYDROSPHERE_ENDPOINT'),
        string(credentialsId: 'HydroIntegrationsAWSRegion', variable: 'AWS_DEFAULT_REGION'),
        string(credentialsId: 'HydroIntegrationsS3DataCaptureBucket', variable: 'S3_DATA_CAPTURE_BUCKET'),
        string(credentialsId: 'HydroIntegrationsS3DataCapturePrefix', variable: 'S3_DATA_CAPTURE_PREFIX'),
        string(credentialsId: 'HydroIntegrationsS3DataTrainingBucket', variable: 'S3_DATA_TRAINING_BUCKET'),
        string(credentialsId: 'HydroIntegrationsS3DataTrainingPrefix', variable: 'S3_DATA_TRAINING_PREFIX'),
        [
            $class: 'AmazonWebServicesCredentialsBinding',
            credentialsId: 'aws-hydrosphere-jenkins-credentials',
            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
        ],
    ]) {
        sh """#!/bin/bash
            set -ex

            # prepare environment
            pyenv install --skip-existing 3.6.10
            pyenv install --skip-existing 3.7.7
            pyenv install --skip-existing 3.8.2
            eval "\$(pyenv init -)"
            pyenv shell 3.6.10 3.7.7 3.8.2
            
            python -m venv venv
            source venv/bin/activate
            pip install wheel~=0.34.2
            pip install tox~=3.14.5
            pip install aws-sam-cli~=0.47.0

            # run tests for lambda distribution
            # and for hydro-integrations sdk
            tox

            # check that lambda distribution
            # can be built
            cd scripts/aws/traffic_shadowing
            ./sam-build.sh
            cd ../../../

            # check that hydro-integrations
            # sdk can be built
            pip install -r requirements.txt
            python setup.py bdist_wheel
            deactivate
        """
    }
}

def collectTestResults = {
    junit testResults: 'test-report.xml', allowEmptyResults: true
}

pipelineCommon(
    repository,
    false, //needSonarQualityGate,
    [],
    collectTestResults,
    buildAndPublishReleaseFunction,
    buildFunction,
    buildFunction
)