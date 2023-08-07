import yaml

data = b"!!python/object/apply:subprocess.Popen \\n- ls"
deserialized_data = yaml.load(data, Loader=yaml.Loader)
