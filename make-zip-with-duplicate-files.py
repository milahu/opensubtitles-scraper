import zipfile
zip = zipfile.ZipFile('abc.zip', 'w')
for i in range(0, 10):
  zip.writestr('myfile', f'This is sample text {i}')
zip.close()

