def repository = 'hydro-serving-integrations'

def buildAndPublishReleaseFunction = {
    configFileProvider([configFile(fileId: 'PYPIDeployConfiguration', targetLocation: '.pypirc', variable: 'PYPI_SETTINGS')]) {
        sh """#!/bin/bash
        python3 -m venv venv
        source venv/bin/activate
        pip install wheel~=0.34.2
        pip install tox~=3.14.5
        tox
        pip install -r requirements.txt
        python setup.py bdist_wheel
        python -m twine upload --config-file ${env.WORKSPACE}/.pypirc -r pypi ${env.WORKSPACE}/dist/*
        deactivate
    """
    }
}

def buildFunction = {
    sh """#!/bin/bash
        python3 -m venv venv
        source venv/bin/activate
        pip install wheel~=0.34.2
        pip install tox~=3.14.5
        
        tox
        pip install -r requirements.txt
        python setup.py bdist_wheel
        deactivate
    """
}

def collectTestResults = {
    junit testResults: 'test-report.xml', allowEmptyResults: true
}

pipelineCommon(
    repository,
    false, //needSonarQualityGate,
    [],
    collectTestResults,
    buildFunction,
    buildFunction,
    buildFunction
)