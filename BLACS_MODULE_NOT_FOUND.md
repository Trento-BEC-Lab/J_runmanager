# Fixing `ModuleNotFoundError: blacs`

## Problem

Running the `blacs` command produced:

```text
ModuleNotFoundError: blacs
```

The launcher uses `desktop-app`, which tries to locate the installed `blacs` Python package. The `labscript_test_v1` environment contained an editable installation whose generated package finder pointed to an old path:

```text
/home/bec/labscript_install/J_blacs/blacs
```

However, the current checkout was located at:

```text
/home/bec/SOFTWARE/labscript_install/J_blacs/blacs
```

Because the old path no longer existed, Python could not find the `blacs` module when the launcher was started.

## Solution

Reinstall BLACS as an editable package from its current checkout using the same Python environment that runs the launcher:

```bash
/home/bec/.local/share/mamba/envs/labscript_test_v1/bin/python \
    -m pip install --editable /home/bec/SOFTWARE/labscript_install/J_blacs
```

This regenerates the editable-install metadata with the correct source path.

## Verification

Check that the module resolves to the current checkout:

```bash
cd /tmp
/home/bec/.local/share/mamba/envs/labscript_test_v1/bin/python -c \
    "import blacs; print(blacs.__file__)"
```

The output should reference:

```text
/home/bec/SOFTWARE/labscript_install/J_blacs/blacs/__init__.py
```

BLACS can then be started normally:

```bash
blacs
```

## Prevention

After moving a source checkout, refresh any editable installation associated with it. Otherwise, generated `site-packages` metadata may continue to reference the previous directory.
