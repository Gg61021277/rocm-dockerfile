# rocm-dockerfile

https://medium.com/@gg77021277/building-a-docker-container-with-common-tools-for-machine-learning-on-amd-rx-7900-xtx-seamless-0b724206f3c4

A generic docker file that makes the user feel at home


1. Create the private store for your container by bootstrapping from your local hosts private files ( dot files )

(on host)./bootstrap_container_store.py

2. Build the Container

(on host)make buildtorch-rocm-addon

3. Run the Container. 

(ion host)make runtorch-rocm-addon

4. Run the terminator in the container

(in container)nohup terminator &

