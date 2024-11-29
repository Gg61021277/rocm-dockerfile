# rocm-dockerfile
A generic docker file that makes the user feel at home


-Create the private store for your container by bootstrapping from your local hosts private files ( dot files )

(on host)./bootstrap_container_store.py

-Build the Container

(on host)make buildtorch-rocm-addon

-Run the Container. 

(ion host)make runtorch-rocm-addon

-Run the terminator in the container

(in container)nohup terminator &

