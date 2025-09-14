mkdir -p build && cd build 
cmake ..
make 
mv ./gasgen ../gasgen
mv ./gastask ../gastask
