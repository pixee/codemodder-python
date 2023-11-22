import tempfile
path = tempfile.NamedTemporaryFile().name
file = open(path, 'w', encoding='utf-8')
pass
file.write('Hello World')
