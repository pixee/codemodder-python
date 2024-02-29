The default loaders in PyYAML are not safe to use with untrusted data. They potentially make your application vulnerable to arbitrary code execution attacks. If you open a YAML file from an untrusted source, and the file is loaded with the default loader, an attacker could execute arbitrary code on your machine.

This codemod hardens all [`yaml.load()`](https://pyyaml.org/wiki/PyYAMLDocumentation) calls against such attacks by replacing the default loader with `yaml.SafeLoader`. This is the recommended loader for loading untrusted data. For most use cases it functions as a drop-in replacement for the default loader.

Calling `yaml.load()` without an explicit loader argument is equivalent to calling it with `Loader=yaml.Loader`, which is unsafe. This usage [has been deprecated](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input\)-Deprecation) since PyYAML 5.1. This codemod will add an explicit `SafeLoader` argument to all `yaml.load()` calls that don't use an explicit loader.

The changes from this codemod look like the following:
```diff
  import yaml
  data = b'!!python/object/apply:subprocess.Popen \\n- ls'
- deserialized_data = yaml.load(data, yaml.Loader)
+ deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
```
