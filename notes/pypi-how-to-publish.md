# How to Publish kinnoo to PyPI

## 1. Build the distribution artifacts

```
python3 -m build
```

## 2. Upload to PyPI using twine

```
python3 -m twine upload dist/*
```

- You’ll need your PyPI credentials (username and password or API token).
- If you haven’t installed the build or twine tools yet, do:

```
python3 -m pip install build twine
```

## 3. (Optional) Test upload to TestPyPI

```
python3 -m twine upload --repository testpypi dist/*
```

- For more info, see: https://packaging.python.org/en/latest/tutorials/packaging-projects/
