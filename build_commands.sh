mkdir -p tmp
mkdir -p build && cd build 
cmake ..
make 
mv ./gasgen ../tmp
mv ./gastask ../tmp
cd ../tmp
cp ../gastask.conf.tmpl ./gastask.conf
./gasgen ./gastask.conf