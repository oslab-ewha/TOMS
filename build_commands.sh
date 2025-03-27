mkdir -p build && cd build 
cmake ..
make 
mv ./gasgen ..
mv ./gastask ..