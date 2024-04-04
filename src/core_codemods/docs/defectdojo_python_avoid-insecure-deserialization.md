Use of insecure deserialization can potentially lead to arbitrary code execution. This codemod addresses this issue with two different serialization providers:
* `yaml` (via [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation))
* `pickle` (via the standard library [pickle](https://docs.python.org/3/library/pickle.html) module)

Each is described in more detail below.

## PyYAML

The default loaders in PyYAML are not safe to use with untrusted data. They potentially make your application vulnerable to arbitrary code execution attacks. If you open a YAML file from an untrusted source, and the file is loaded with the default loader, an attacker could execute arbitrary code on your machine.

Calling `yaml.load()` without an explicit loader argument is equivalent to calling it with `Loader=yaml.Loader`, which is unsafe. This usage [has been deprecated](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input\)-Deprecation) since PyYAML 5.1. This codemod will add an explicit `SafeLoader` argument to all `yaml.load()` calls that don't use an explicit loader.

The changes from this codemod look like the following:
```diff
  import yaml
  data = b'!!python/object/apply:subprocess.Popen \\n- ls'
- deserialized_data = yaml.load(data, yaml.Loader)
+ deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
```

## Pickle

Python's `pickle` module is notoriouly insecure. While it is very useful for serializing and deserializing Python objects, it is not safe to use `pickle` to load data from untrusted sources. This is because `pickle` can execute arbitrary code when loading data. This can be exploited by an attacker to execute arbitrary code on your system. Unlike `yaml` there is no concept of a "safe" loader in `pickle`. Therefore, it is recommended to avoid `pickle` and to use a different serialization format such as `json` or `yaml` when working with untrusted data.

However, if you must use `pickle` to load data from an untrusted source, we recommend using the open-source `fickling` library. `fickling` is a drop-in replacement for `pickle` that validates the data before loading it and checks for the possibility of code execution. This makes it much safer (although still not entirely safe) to use `pickle` to load data from untrusted sources.

This codemod replaces calls to `pickle.load` with `fickling.load` in Python code. It also adds an import statement for `fickling` if it is not already present. 

The changes look like the following:
```diff
- import pickle
+ import fickling
 
- data = pickle.load(file)
+ data = fickling.load(file)
```
