rm -rf dist/*
python3 setup.py sdist
python3 setup.py bdist_wheel
twine upload --repository pypi dist/*
