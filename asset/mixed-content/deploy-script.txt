rm -rf dist/* .ansar-home/bin/* .ansar-home/bin/.storage-manifest.json 
make
tree .ansar-home/bin
mkdir dist/folder
make
tree .ansar-home/bin
touch dist/folder/file
make
tree .ansar-home/bin
chmod 774 dist/folder/file
make
ls -l .ansar-home/bin/folder/file
rm dist/folder/file
make
tree .ansar-home/bin
rmdir dist/folder
make
tree .ansar-home/bin
mkdir dist/folder
make
tree .ansar-home/bin
ls -ld .ansar-home/bin/folder
chmod 751 dist/folder
make
ls -ld .ansar-home/bin/folder
touch dist/folder/file
make
tree .ansar-home/bin
rm dist/folder/file
mkdir dist/folder/file
make
tree .ansar-home/bin
rmdir dist/folder/file
touch dist/folder/file
make
tree .ansar-home/bin

