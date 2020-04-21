def repository = 'hydro-serving-integrations'

def buildAndPublishReleaseFunction = {
    configFileProvider([configFile(fileId: 'PYPIDeployConfiguration', targetLocation: '.pypirc', variable: 'PYPI_SETTINGS')]) {
        sh """#!/bin/bash
        set -e

        # prepare environment
        export PY_36=3.6.10
        export PY_37=3.7.7
        export PY_38=3.8.2
        pyenv install --skip-existing $PY_36
        pyenv install --skip-existing $PY_37
        pyenv install --skip-existing $PY_38
        eval "$(pyenv init -)"
        pyenv shell $PY_36 $PY_37 $PY_38
        
        python -m venv venv
        source venv/bin/activate
        pip install wheel~=0.34.2
        pip install tox~=3.14.5

        # run tests for lambda distribution
        # and for hydro-integrations sdk
        tox

        # build lambda distribution artifacts
        cd scrips/aws/traffic_shadowing
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

def buildFunction = {
    sh """#!/bin/bash
        set -e

        # prepare environment
        export PY_36=3.6.10
        export PY_37=3.7.7
        export PY_38=3.8.2
        pyenv install --skip-existing $PY_36
        pyenv install --skip-existing $PY_37
        pyenv install --skip-existing $PY_38
        eval "$(pyenv init -)"
        pyenv shell $PY_36 $PY_37 $PY_38
        
        python -m venv venv
        source venv/bin/activate
        pip install wheel~=0.34.2
        pip install tox~=3.14.5

        # run tests for lambda distribution
        # and for hydro-integrations sdk
        tox

        # check that lambda distribution
        # can be built
        cd scrips/aws/traffic_shadowing
        ./sam-build.sh
        ./sam-package.sh
        cd ../../../

        # check that hydro-integrations
        # sdk can be built
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
    buildAndPublishReleaseFunction,
    buildFunction,
    buildFunction
)