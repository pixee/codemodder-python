This codemod hardens all [`yaml.load()`](https://pyyaml.org/wiki/PyYAMLDocumentation) calls against attacks that could result from deserializing untrusted data.

The fix uses a safety check that already exists in the `yaml` module, replacing unsafe loader class with `SafeLoader`.
The changes from this codemod look like this:

```diff
  import yaml
  data = b'!!python/object/apply:subprocess.Popen \\n- ls'
- deserialized_data = yaml.load(data, yaml.Loader)
+ deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
```
The codemod will also catch if you pass in the loader argument as a kwarg and if you use any loader other than `SafeLoader`,
including `FullLoader` and `UnsafeLoader`.
